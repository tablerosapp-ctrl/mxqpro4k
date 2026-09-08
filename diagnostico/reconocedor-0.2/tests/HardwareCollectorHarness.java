package com.tvbase.reconocimiento;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.concurrent.Callable;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

/** Host JVM tests for actual worker bookkeeping and bounded memory reads only. */
public final class HardwareCollectorHarness {
    private static int cases;
    private static void require(boolean value, String reason) {
        if (!value) throw new AssertionError(reason);
    }
    private static void waitIdle() throws Exception {
        long end = System.nanoTime() + TimeUnit.SECONDS.toNanos(2);
        while (HardwareCollector.hasPendingReads() && System.nanoTime() < end) Thread.sleep(1);
        require(!HardwareCollector.hasPendingReads(), "worker slot did not clear after actual completion");
    }
    private static void successfulAndExceptionalActions() throws Exception {
        for (int i = 0; i < 100; i++) {
            String value = HardwareCollector.readBounded("success", 1000, new Callable<String>() {
                public String call() { return "memory-only"; }
            });
            require("memory-only".equals(value), "result was not delivered");
            require(!HardwareCollector.hasPendingReads(), "normal sequential completion left occupied slot");
        }
        try {
            HardwareCollector.readBounded("failure", 1000, new Callable<String>() {
                public String call() throws IOException { throw new IOException("fixture error"); }
            });
            throw new AssertionError("exception accepted");
        } catch (IOException expected) { require(expected.getMessage().equals("fixture error"), "exception wrapping changed"); }
        waitIdle(); cases++;
    }
    private static void timeoutDoesNotReleaseStuckWorker() throws Exception {
        final CountDownLatch release = new CountDownLatch(1);
        final AtomicInteger completed = new AtomicInteger();
        final AtomicInteger duplicateActions = new AtomicInteger();
        final AtomicBoolean cancelled = new AtomicBoolean();
        long began = System.nanoTime();
        try {
            HardwareCollector.readBounded("ignores-interrupt", 30, new Callable<String>() {
                public String call() throws Exception {
                    try {
                        for (;;) {
                            try { release.await(); break; }
                            catch (InterruptedException ignored) { cancelled.set(true); }
                        }
                        return "late memory result";
                    } finally { completed.incrementAndGet(); }
                }
            });
            throw new AssertionError("blocked operation did not time out");
        } catch (TimeoutException expected) { }
        require(System.nanoTime() - began < TimeUnit.SECONDS.toNanos(2), "client remained blocked");
        require(HardwareCollector.hasPendingReads(), "cancelling the Future prematurely freed its worker slot");
        for (int i = 0; i < 20; i++) {
            try {
                HardwareCollector.readBounded("must-not-start", 30, new Callable<String>() {
                    public String call() { duplicateActions.incrementAndGet(); return "wrong"; }
                });
                throw new AssertionError("a second read started while first action remained blocked");
            } catch (HardwareCollector.PendingReadException expected) { }
        }
        require(duplicateActions.get() == 0 && completed.get() == 0, "new or queued observations ran");
        release.countDown(); waitIdle();
        require(completed.get() == 1 && cancelled.get(), "underlying action was not allowed to finish honestly");
        require("next".equals(HardwareCollector.readBounded("after-finish", 1000, new Callable<String>() {
            public String call() { return "next"; }
        })), "slot was not reusable after real completion");
        cases++;
    }
    private static void callerInterruptionDoesNotReleaseWorker() throws Exception {
        final CountDownLatch entered = new CountDownLatch(1), release = new CountDownLatch(1);
        final AtomicBoolean preservedInterrupt = new AtomicBoolean();
        final AtomicBoolean wrong = new AtomicBoolean();
        Thread caller = new Thread(new Runnable() {
            public void run() {
                try {
                    HardwareCollector.readBounded("caller-interrupt", 1000, new Callable<String>() {
                        public String call() {
                            entered.countDown();
                            for (;;) {
                                try { release.await(); break; }
                                catch (InterruptedException ignored) { }
                            }
                            return "late";
                        }
                    });
                    wrong.set(true);
                } catch (InterruptedException expected) { preservedInterrupt.set(Thread.currentThread().isInterrupted()); }
                catch (Exception unexpected) { wrong.set(true); }
            }
        });
        caller.start(); require(entered.await(1, TimeUnit.SECONDS), "worker did not start");
        caller.interrupt(); caller.join(1000);
        require(!caller.isAlive() && preservedInterrupt.get() && !wrong.get(), "caller interruption was not preserved");
        require(HardwareCollector.hasPendingReads(), "caller interruption freed still-running worker");
        release.countDown(); waitIdle(); cases++;
    }
    private static void boundedBytesAndNoProgress() throws Exception {
        for (int count : new int[]{0, 1, 6, 7, 8, 20}) {
            byte[] input = new byte[count];
            byte[] result = HardwareCollector.readBytes(new ByteArrayInputStream(input), 7);
            require(result.length == Math.min(count, 8), "cap+1 truncation sentinel incorrect");
        }
        try {
            HardwareCollector.readBytes(new InputStream() {
                public int read() { return 0; }
                public int read(byte[] bytes, int offset, int length) { return 0; }
            }, 7);
            throw new AssertionError("zero-progress stream did not fail");
        } catch (IOException expected) { }
        Thread.currentThread().interrupt();
        try {
            HardwareCollector.readBytes(new ByteArrayInputStream(new byte[]{1}), 7);
            throw new AssertionError("interrupted stream was read");
        } catch (IOException expected) { }
        finally { Thread.interrupted(); }
        cases++;
    }
    private static void invalidLimitsNeverStartActions() throws Exception {
        for (long timeout : new long[]{-1, 0, 30001}) {
            try {
                HardwareCollector.readBounded("invalid", timeout, new Callable<String>() {
                    public String call() { throw new AssertionError("invalid action started"); }
                });
                throw new AssertionError("invalid timeout accepted");
            } catch (IllegalArgumentException expected) { }
        }
        for (int cap : new int[]{0, -1, 1048577}) {
            try { HardwareCollector.readBytes(new ByteArrayInputStream(new byte[]{1}), cap); throw new AssertionError("invalid cap accepted"); }
            catch (IOException expected) { }
        }
        require(!HardwareCollector.hasPendingReads(), "invalid action occupied slot"); cases++;
    }
    public static void main(String[] args) throws Exception {
        successfulAndExceptionalActions();
        timeoutDoesNotReleaseStuckWorker();
        callerInterruptionDoesNotReleaseWorker();
        boundedBytesAndNoProgress();
        invalidLimitsNeverStartActions();
        System.out.println("PASS HardwareCollector/0.2 host worker and byte-bound cases=" + cases);
    }
}
