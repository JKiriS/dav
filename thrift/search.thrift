include "common.thrift"

service Search {
    common.Result search(1:string wd, 2:string id),
    common.Result updateSearchIndex()
}