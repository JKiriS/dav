include "common.thrift"

service Rec {
    common.Result updateRList(1:string uid) throws (1:common.DataError de),

    common.Result updateDic(1:i32 batch_size, 2:i32 skip),

    common.Result updateTfIdf(1:i32 batch_size) throws (1:common.DataError de),

    common.Result updateModel(1:i32 batch_size, 2:i32 num_topics) throws (1:common.FileError fe),   

    common.Result lsiSearch(1:string query, 2:i32 start, 3:i32 length) throws (1:common.DataError de, 2:common.FileError fe)

	common.Result updateUPre(1:string uid),
}