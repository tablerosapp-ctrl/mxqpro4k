package com.tvbase.reconocimiento;

/** A closed baseline must reach the selected destination before optional hardware observations.
 * The explicit local-copy mode does not assert USB export. Each stage owns its own immutable archive; no background writer is accepted. */
public final class CaptureSequence {
    public interface Steps {
        void saveBaseline() throws Exception;
        void exportBaseline() throws Exception;
        void saveInventory() throws Exception;
        void exportInventory() throws Exception;
    }
    private CaptureSequence() {}
    public static void run(Steps steps) throws Exception {
        steps.saveBaseline();
        steps.exportBaseline();
        steps.saveInventory();
        steps.exportInventory();
    }
}
