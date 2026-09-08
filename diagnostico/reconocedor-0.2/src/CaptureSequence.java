package com.tvbase.reconocimiento;

/** A closed baseline must reach USB before any optional hardware observation.
 * Each stage owns its own immutable archive; no background writer is accepted. */
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
