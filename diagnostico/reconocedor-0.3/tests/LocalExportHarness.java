package com.tvbase.reconocimiento;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.util.Arrays;
import org.json.JSONObject;

/** Actual local-export Java code, with small regular host files only. */
public final class LocalExportHarness {
    private static int cases,symlinkSkipped;
    private static void require(boolean ok,String why){if(!ok)throw new AssertionError(why);}
    private static File dir(File parent,String name)throws Exception{File f=new File(parent,name);require(f.mkdir(),"fresh directory");return f;}
    private static void put(File file,byte[] data)throws Exception{try(FileOutputStream out=new FileOutputStream(file)){out.write(data);out.getFD().sync();}}
    private static void rejected(File downloads,ReportArchive.Result archive)throws Exception{
        try{LocalExport.save(downloads,archive);throw new AssertionError("invalid export accepted");}catch(IOException expected){}cases++;
    }
    public static void main(String[] args)throws Exception{
        require(args.length==1,"output required");File root=new File(args[0]);require(root.mkdir(),"fresh output");
        File sources=dir(root,"sources"),session=dir(sources,"11111111-1111-4111-8111-111111111111");
        JSONObject report=new JSONObject().put("suggested_profile","desconocido")
            .put("capture_id",session.getName()).put("device_id","22222222-2222-4222-8222-222222222222")
            .put("schema","tvbase-recognition-1").put("capture_state","basic_checkpoint");
        ReportArchive.Result archive=ReportArchive.build(session,report);
        byte[] original=Files.readAllBytes(archive.archive.toPath());
        File downloads=dir(root,"downloads");
        LocalExport.Result copied=LocalExport.save(downloads,archive);
        require(copied.zip.getParentFile().equals(new File(downloads,LocalExport.FOLDER)),"wrong folder");
        require(Arrays.equals(original,Files.readAllBytes(copied.zip.toPath())),"ZIP bytes differ");
        JSONObject receipt=new JSONObject(new String(Files.readAllBytes(copied.receipt.toPath()),"UTF-8"));
        require("android_downloads".equals(receipt.getString("destination")),"wrong destination claim");
        require(!receipt.getBoolean("usb_copy_verified")&&!receipt.getBoolean("directory_sync_verified"),"false physical claim");
        require(receipt.getBoolean("file_sync_verified")&&receipt.getBoolean("local_readback_sha256_verified"),"missing local evidence");
        require(copied.fileSynced&&copied.readbackVerified&&!copied.directorySynced&&!copied.usbCopyVerified,"result flags");
        require(copied.zip.getParentFile().list().length==2,"unexpected marker or partial after success");cases++;
        byte[] proof=Files.readAllBytes(copied.receipt.toPath());long modified=copied.zip.lastModified();
        LocalExport.Result reused=LocalExport.save(downloads,archive);
        require(reused.zip.equals(copied.zip)&&Arrays.equals(proof,Files.readAllBytes(copied.receipt.toPath()))
            &&Arrays.equals(original,Files.readAllBytes(copied.zip.toPath()))&&modified==copied.zip.lastModified(),"reuse overwrote files");cases++;

        File other=dir(root,"different");File occupied=dir(other,LocalExport.FOLDER);
        File conflicting=new File(occupied,archive.archive.getName());put(conflicting,new byte[]{9,8,7});
        rejected(other,archive);require(Arrays.equals(new byte[]{9,8,7},Files.readAllBytes(conflicting.toPath())),"changed conflicting file");
        require(occupied.list().length==1,"wrote despite conflicting ZIP");

        File incomplete=dir(root,"bad-receipt");LocalExport.Result target=LocalExport.save(incomplete,archive);
        put(target.receipt,"{".getBytes("UTF-8"));
        try{LocalExport.save(incomplete,archive);throw new AssertionError("truncated receipt accepted");}catch(Exception expected){require(!(expected instanceof RuntimeException)||!(expected instanceof IllegalStateException),"unexpected test exception");}
        require("{".equals(new String(Files.readAllBytes(target.receipt.toPath()),"UTF-8")),"receipt overwritten");cases++;

        File wrong=dir(root,"wrong-claim");LocalExport.Result flagged=LocalExport.save(wrong,archive);
        JSONObject wrongReceipt=new JSONObject(new String(Files.readAllBytes(flagged.receipt.toPath()),"UTF-8"));
        put(flagged.receipt,wrongReceipt.put("usb_copy_verified",true).toString().getBytes("UTF-8"));
        rejected(wrong,archive);

        File changed=dir(root,"source-change");put(archive.archive,new byte[]{1,2,3});
        rejected(changed,archive);require(changed.list().length==0,"created output for changed source");put(archive.archive,original);
        rejected(new File(root,"missing-downloads"),archive);
        require(!new File(root,"missing-downloads").exists(),"created Downloads itself");
        File parentFile=new File(root,"not-directory");put(parentFile,new byte[]{1});rejected(parentFile,archive);
        File blocked=dir(root,"occupied-folder");put(new File(blocked,LocalExport.FOLDER),new byte[]{6});rejected(blocked,archive);
        rejected(dir(root,"bad-sha"),new ReportArchive.Result(archive.archive,archive.bytes,"z"));
        rejected(dir(root,"bad-size"),new ReportArchive.Result(archive.archive,-1,archive.sha256));
        File raw=new File(sources,"userdata.img");put(raw,original);
        rejected(dir(root,"raw-image"),new ReportArchive.Result(raw,raw.length(),ReportArchive.sha(raw)));

        File orphan=dir(root,"receipt-without-zip"),orphanFolder=dir(orphan,LocalExport.FOLDER);
        put(new File(orphanFolder,archive.archive.getName()+".local.json"),proof);rejected(orphan,archive);
        require(orphanFolder.list().length==1,"reconstructed orphan receipt automatically");

        File outside=dir(root,"outside"),linked=dir(root,"symlink-parent"),link=new File(linked,LocalExport.FOLDER);
        try{Files.createSymbolicLink(link.toPath(),outside.toPath());}
        catch(IOException unavailable){symlinkSkipped++;}
        catch(UnsupportedOperationException unavailable){symlinkSkipped++;}
        if(Files.isSymbolicLink(link.toPath())){rejected(linked,archive);require(outside.list().length==0,"followed destination link");}
        require(Arrays.equals(original,Files.readAllBytes(archive.archive.toPath())),"source not preserved");
        System.out.println(new JSONObject().put("state","passed").put("cases",cases).put("symlink_skipped",symlinkSkipped)
            .put("scope","Real Java local copy, sync and SHA readback on host fixtures; no Android permissions, USB, SAF or directory-persistence proof."));
    }
}
