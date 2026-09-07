package main

import("archive/zip";"crypto/sha256";"encoding/hex";"encoding/json";"io";"os";"path/filepath";"testing";"bytes")
func fixture(t *testing.T,change func(*Manifest),corrupt bool)string{
 t.Helper();path:=filepath.Join(t.TempDir(),"update.zip");f,_:=os.Create(path);z:=zip.NewWriter(f);m:=Manifest{Format:1,ID:allowedPackageID,DT:"gxlx2_p291_1g",Media:mediaID};b:=bytes.Repeat([]byte{42},4096);h:=sha256.Sum256(b)
 for _,n:=range names{m.Images=append(m.Images,Image{Name:n,Entry:"tvbase/"+n+".img",Size:int64(len(b)),SHA256:hex.EncodeToString(h[:])});w,_:=z.Create("tvbase/"+n+".img");w.Write(b)}
 if corrupt{m.Images[0].SHA256=hex.EncodeToString(make([]byte,32))};if change!=nil{change(&m)};w,_:=z.Create("tvbase/manifest.json");json.NewEncoder(w).Encode(m);z.Close();f.Close();return path
}
func TestPackageChecks(t *testing.T){
 cases:=[]struct{name string;mutate func(*Manifest)}{{"wrong board",func(m *Manifest){m.DT="gxlx_p271_1g"}},{"bootloader write",func(m *Manifest){m.Images[0].Name="bootloader"}},{"missing partition",func(m *Manifest){m.Images=m.Images[:4]}},{"wrong size",func(m *Manifest){m.Images[0].Size++}},{"wrong media",func(m *Manifest){m.Media="other"}}}
 for _,c:=range cases{t.Run(c.name,func(t *testing.T){if p,e:=loadPackage(fixture(t,c.mutate,false));e==nil{p.ZIP.Close();t.Fatal("unsafe package accepted")}})}
 p,e:=loadPackage(fixture(t,nil,false));if e!=nil{t.Fatal(e)};defer p.ZIP.Close();if e=p.verify();e!=nil{t.Fatal(e)}
 bad,e:=loadPackage(fixture(t,nil,true));if e!=nil{t.Fatal(e)};defer bad.ZIP.Close();if bad.verify()==nil{t.Fatal("bad hash accepted")}
}
func TestExactCopy(t *testing.T){if _,e:=copyExact(io.Discard,bytes.NewReader([]byte{1}),2,nil);e==nil{t.Fatal("short source accepted")};if _,e:=copyExact(shortWriter{},bytes.NewReader([]byte{1,2}),2,nil);e==nil{t.Fatal("short write accepted")}}
type shortWriter struct{};func(shortWriter)Write(b []byte)(int,error){return len(b)-1,nil}
