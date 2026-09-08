package com.tvbase.reconocimiento;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import java.util.zip.ZipFile;
import org.json.JSONObject;

/** Host-only execution of the actual sequence and ZIP writer. USB is a fake port. */
public final class CaptureSequenceHarness {
    private static int cases;
    private static final String[] ORDER={"save_baseline","export_baseline","save_inventory","export_inventory"};
    private static void require(boolean ok,String why){if(!ok)throw new AssertionError(why);}

    private static final class Probe implements CaptureSequence.Steps {
        final List<String> seen=new ArrayList<String>();
        final int failure;
        final IOException cause=new IOException("injected fixture failure");
        Probe(int failure){this.failure=failure;}
        void step(int position)throws Exception {
            require(seen.size()==position,"out of order or repeated stage");
            seen.add(ORDER[position]);
            if(position==failure)throw cause;
        }
        public void saveBaseline()throws Exception{step(0);}
        public void exportBaseline()throws Exception{step(1);}
        public void saveInventory()throws Exception{step(2);}
        public void exportInventory()throws Exception{step(3);}
    }

    private static void failuresStopLaterStages()throws Exception {
        for(int failure=0;failure<4;failure++){
            Probe probe=new Probe(failure);
            try{CaptureSequence.run(probe);throw new AssertionError("failure swallowed");}
            catch(IOException actual){require(actual==probe.cause,"original failure not preserved");}
            require(probe.seen.equals(Arrays.asList(ORDER).subList(0,failure+1)),"stage continued after failure");
            cases++;
        }
        Probe probe=new Probe(-1);CaptureSequence.run(probe);
        require(probe.seen.equals(Arrays.asList(ORDER)),"successful order");cases++;
    }

    private static void exportIsBarrier()throws Exception {
        final CountDownLatch reached=new CountDownLatch(1),release=new CountDownLatch(1);
        final AtomicReference<Throwable> failure=new AtomicReference<Throwable>();
        final List<String> seen=new ArrayList<String>();
        Thread thread=new Thread(new Runnable(){public void run(){try{
            CaptureSequence.run(new CaptureSequence.Steps(){
                public void saveBaseline(){seen.add("saved");}
                public void exportBaseline()throws Exception{
                    seen.add("exporting");reached.countDown();
                    if(!release.await(5,TimeUnit.SECONDS))throw new IOException("fixture release timeout");
                    throw new IOException("baseline export failed after waiting");
                }
                public void saveInventory(){throw new AssertionError("inventory started before USB success");}
                public void exportInventory(){throw new AssertionError("inventory export after failure");}
            });
        }catch(Throwable e){failure.set(e);}}},"sequence-host-fixture");
        thread.start();
        try{require(reached.await(5,TimeUnit.SECONDS),"did not reach export barrier");
            require(seen.equals(Arrays.asList("saved","exporting")),"unexpected stage at barrier");
        }finally{release.countDown();thread.join(5000);}
        require(!thread.isAlive(),"fixture thread leaked");
        require(failure.get() instanceof IOException,"failure did not leave sequence");cases++;
    }

    private static JSONObject report(String capture,String stage)throws Exception {
        return new JSONObject().put("schema","tvbase-recognition-1").put("recognizer_version","0.2")
            .put("capture_id",capture).put("device_id","12345678-1234-1234-1234-123456789abc")
            .put("suggested_profile","desconocido").put("capture_state",stage)
            .put("hardware",new JSONObject().put("state","fixture_only"));
    }
    private static File directory(File parent,String name)throws Exception {
        File result=new File(parent,name);require(result.mkdir(),"fixture directory occupied");return result;
    }
    private static void archivesAreSeparate(File root)throws Exception {
        File captures=directory(root,"archives");
        String initialId="11111111-1111-4111-8111-111111111111";
        String fullId="22222222-2222-4222-8222-222222222222";
        File initial=directory(captures,initialId),full=directory(captures,fullId);
        ReportArchive.Result baseline=ReportArchive.build(initial,report(initialId,"basic_checkpoint"));
        byte[] before=Files.readAllBytes(baseline.archive.toPath());
        ReportArchive.Result inventory=ReportArchive.build(full,report(fullId,"inventory_with_explicit_limits").put("parent_capture_id",initialId));
        require(!baseline.archive.equals(inventory.archive),"stage archive collision");
        require(Arrays.equals(before,Files.readAllBytes(baseline.archive.toPath())),"baseline changed by inventory build");
        require(baseline.sha256.equals(ReportArchive.sha(baseline.archive)),"baseline SHA changed");
        try(ZipFile archive=new ZipFile(inventory.archive)){
            require(archive.size()==2&&archive.getEntry("informe.json")!=null&&archive.getEntry("manifest.json")!=null,"unexpected raw files in small fixture");
        }
        cases++;
        try{ReportArchive.build(initial,report(initialId,"basic_checkpoint"));throw new AssertionError("session overwrite accepted");}
        catch(IOException expected){}
        require(Arrays.equals(before,Files.readAllBytes(baseline.archive.toPath())),"failed repeat damaged baseline");cases++;

        // Different UUIDs can share the short ZIP-name prefix. Existing ZIP must survive.
        String collidingId="11111111-2222-4222-8222-222222222222";
        File collision=directory(captures,collidingId);
        try{ReportArchive.build(collision,report(collidingId,"basic_checkpoint"));throw new AssertionError("short-name collision overwritten");}
        catch(IOException expected){}
        require(Arrays.equals(before,Files.readAllBytes(baseline.archive.toPath())),"name collision damaged original");cases++;

        final ReportArchive.Result[] held={baseline};
        final IOException failure=new IOException("optional inventory unavailable");
        try{CaptureSequence.run(new CaptureSequence.Steps(){
            public void saveBaseline()throws Exception{require(held[0].archive.isFile(),"missing checkpoint");}
            public void exportBaseline()throws Exception{require(held[0].sha256.equals(ReportArchive.sha(held[0].archive)),"changed checkpoint");}
            public void saveInventory()throws Exception{throw failure;}
            public void exportInventory(){throw new AssertionError("export after inventory failure");}
        });throw new AssertionError("inventory failure swallowed");}catch(IOException actual){require(actual==failure,"wrong failure");}
        require(Arrays.equals(before,Files.readAllBytes(baseline.archive.toPath())),"inventory failure damaged checkpoint");cases++;
    }
    public static void main(String[] args)throws Exception {
        require(args.length==1,"fresh host output required");
        File root=new File(args[0]);require(root.mkdir(),"host fixture already exists");
        failuresStopLaterStages();exportIsBarrier();archivesAreSeparate(root);
        System.out.println(new JSONObject().put("state","passed").put("cases",cases)
            .put("scope","Actual CaptureSequence and ReportArchive on host; fake USB/export ports. No Android UI, SAF, device filesystem, or physical USB claim."));
    }
}
