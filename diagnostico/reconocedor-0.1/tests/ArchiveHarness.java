package com.tvbase.reconocimiento;
import java.io.*;
import java.util.*;
import org.json.*;

public class ArchiveHarness {
    static void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    public static void main(String[] args)throws Exception {
        File root=new File(args[0]);require(root.mkdir(),"fresh fixture output");
        File session=new File(root,UUID.randomUUID().toString());require(session.mkdir(),"session");
        File drivers=new File(session,"drivers");require(drivers.mkdir(),"drivers");
        File details=new File(session,"details");require(details.mkdir(),"details");
        ReportArchive.write(new File(details,"dato.json"),"{\"estado\":\"observado\",\"texto\":\"áéíóú\"}");
        try(FileOutputStream f=new FileOutputStream(new File(drivers,"fixture.bin"))){byte[] data=new byte[4194304];new Random(71).nextBytes(data);f.write(data);f.getFD().sync();}
        JSONObject report=new JSONObject().put("schema","tvbase-recognition-1").put("capture_id",UUID.randomUUID().toString()).put("device_id",UUID.randomUUID().toString()).put("suggested_profile","p291").put("profile_confidence","declared").put("display_name","Fixture parcial").put("android",new JSONObject().put("api",28)).put("hardware",new JSONObject().put("denied",1)).put("webview",new JSONObject().put("state","not_available")).put("export_limits",new JSONObject().put("full_rom_backup",false));
        ReportArchive.Result result=ReportArchive.build(session,report);
        require(result.bytes>4194304L,"binary actually stored");require(result.sha256.equals(ReportArchive.sha(result.archive)),"stable archive hash");
        int rejected=0;
        for(String path:new String[]{"details/../escape","details/CON.txt","details/stream:extra","details/trailing.","details/bad|name","outside/file"}){
            try{ReportArchive.safePath(session,new File(session,path));}catch(IOException expected){rejected++;}
        }
        require(rejected==6,"reject unsafe names");
        boolean duplicate=false;try{ReportArchive.build(session,report);}catch(IOException expected){duplicate=true;}
        require(duplicate,"do not overwrite capture");
        require(result.sha256.equals(ReportArchive.sha(result.archive)),"failed retry preserved finished zip");
        System.out.println(new JSONObject().put("state","passed").put("archive",result.archive.getAbsolutePath()).put("bytes",result.bytes).put("sha256",result.sha256).put("unsafe_paths_rejected",rejected).put("overwrite_rejected",duplicate));
    }
}
