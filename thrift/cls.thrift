include "common.thrift"

service Cls {
    common.Result updateClassifyDic(),
    common.Result trainClassify() throws (1:common.DataError de, 2:common.FileError fe),
    common.Result classify(1:string category) throws (1:common.DataError de, 2:common.FileError fe)
}