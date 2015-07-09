include "common.thrift"

service Rec {
    common.Result updateRList(1:string uid) throws (1:common.DataError de),
    common.Result updateLsiIndex(1:string category) throws (1:common.DataError de, 2:common.FileError fe),
    common.Result updateLsiDic(1:string category) throws (1:common.DataError de),
    common.Result updateUPre(1:string uid),
}