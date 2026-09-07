package main

import (
 "archive/zip"
 "crypto/sha256"
 "encoding/hex"
 "encoding/json"
 "fmt"
 "io"
 "os"
)

const mediaID = "TVBASE-P291-20260906-4dc82786"
var allowedPackageID = "TVBASE-P291-A9-0.1" // Set explicitly when building a reviewed revision.
type Image struct { Name string `json:"name"`; Entry string `json:"entry"`; Size int64 `json:"size"`; SHA256 string `json:"sha256"` }
type Manifest struct { Format int `json:"format"`; ID string `json:"id"`; DT string `json:"dt_id"`; Media string `json:"media_id"`; Images []Image `json:"images"` }
type Package struct { ZIP *zip.ReadCloser; Manifest Manifest; Entries map[string]*zip.File }
var names = []string{"system","vendor","product","odm","boot"} // Kernel last; no bootloader, DTB, recovery, userdata or keys.
func loadPackage(path string) (*Package,error) {
 z,e:=zip.OpenReader(path);if e!=nil{return nil,e};p:=&Package{ZIP:z,Entries:map[string]*zip.File{}}
 fail:=func(e error)(*Package,error){z.Close();return nil,e}
 for _,f:=range z.File {if _,ok:=p.Entries[f.Name];ok{return fail(fmt.Errorf("entrada ZIP duplicada: %s",f.Name))};p.Entries[f.Name]=f}
 f:=p.Entries["tvbase/manifest.json"];if f==nil||f.UncompressedSize64>32768{return fail(fmt.Errorf("manifiesto ausente o invalido"))}
 r,e:=f.Open();if e!=nil{return fail(e)};d:=json.NewDecoder(io.LimitReader(r,32769));d.DisallowUnknownFields();e=d.Decode(&p.Manifest);r.Close();if e!=nil{return fail(e)}
 m:=p.Manifest
 if m.Format!=1||m.ID!=allowedPackageID||m.DT!="gxlx2_p291_1g"||m.Media!=mediaID||len(m.Images)!=len(names){return fail(fmt.Errorf("perfil de paquete no permitido"))}
 for i,im:=range m.Images {
  if im.Name!=names[i]||im.Entry!="tvbase/"+im.Name+".img"||im.Size<4096||im.Size>2<<30{return fail(fmt.Errorf("imagen no permitida: %s",im.Name))}
  hash,e:=hex.DecodeString(im.SHA256);if e!=nil||len(hash)!=32{return fail(fmt.Errorf("SHA256 invalido"))}
  f:=p.Entries[im.Entry];if f==nil||int64(f.UncompressedSize64)!=im.Size{return fail(fmt.Errorf("tamano incorrecto: %s",im.Name))}
 }
 return p,nil
}
func copyExact(dst io.Writer,src io.Reader,n int64,tick func(int64)) (string,error) {
 h:=sha256.New();buf:=make([]byte,1<<20);var done int64
 for done<n {chunk:=int64(len(buf));if n-done<chunk{chunk=n-done};got,e:=io.ReadFull(src,buf[:chunk]);if e!=nil{return "",fmt.Errorf("lectura incompleta en %d: %w",done,e)}
  w,e:=dst.Write(buf[:got]);if e!=nil{return "",e};if w!=got{return "",io.ErrShortWrite};h.Write(buf[:got]);done+=int64(got);if tick!=nil{tick(done)}
 }
 return hex.EncodeToString(h.Sum(nil)),nil
}
func (p *Package) verify()error {
 for _,im:=range p.Manifest.Images {r,e:=p.Entries[im.Entry].Open();if e!=nil{return e};s,e:=copyExact(io.Discard,r,im.Size,nil);if e==nil{var extra [1]byte;n,last:=r.Read(extra[:]);if n!=0||last!=io.EOF{e=fmt.Errorf("final ZIP/CRC invalido: %s",im.Name)}};r.Close();if e!=nil{return e};if s!=im.SHA256{return fmt.Errorf("hash incorrecto: %s",im.Name)}}
 return nil
}
func fileHash(path string,n int64)(string,error){f,e:=os.Open(path);if e!=nil{return "",e};defer f.Close();return copyExact(io.Discard,f,n,nil)}
