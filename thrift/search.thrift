include "common.thrift"

service Search {
    common.Result search(1:string wd, 2:i32 start, 3:i32 length),
    common.Result updateSearchIndex()
}