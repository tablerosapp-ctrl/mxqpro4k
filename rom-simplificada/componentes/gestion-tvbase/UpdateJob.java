package local.tvbase.gestion;
import android.app.job.*;
import android.os.Handler;
import android.os.Looper;
import java.util.concurrent.ConcurrentHashMap;
public final class UpdateJob extends JobService {
    private final ConcurrentHashMap<Integer,ManagerEngine> engines=new ConcurrentHashMap<Integer,ManagerEngine>();
    private final Handler main=new Handler(Looper.getMainLooper());
    @Override public boolean onStartJob(final JobParameters params){
        final ManagerEngine active=new ManagerEngine(this);
        if(engines.putIfAbsent(params.getJobId(),active)!=null)return false;
        new Thread(new Runnable(){public void run(){
            final boolean worked=active.check(true);
            main.post(new Runnable(){public void run(){
                // onStartJob/onStopJob and completion share the main thread; an old generation cannot finish a replacement.
                if(engines.get(params.getJobId())!=active)return;
                engines.remove(params.getJobId(),active);
                if(!active.cancelled.get()){
                    jobFinished(params,!worked);
                    if(worked)ManagerEngine.schedule(UpdateJob.this,params.getJobId()==ManagerEngine.WINDOW_JOB);
                }
            }});
        }},"tvbase-update-job").start();return true;
    }
    @Override public boolean onStopJob(JobParameters params){
        ManagerEngine engine=engines.remove(params.getJobId());
        if(engine!=null)engine.cancel();return true;
    }
}
