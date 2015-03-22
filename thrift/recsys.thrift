service RecSys {
    string updateRList(1:string uid),
    string updateLsiIndex(1:string category),
    string updateLsiDic(1:string category),
    string updateUPre(1:string uid),
    string updateClassifyDic(),
    string trainClassify(),
    string classify(1:string category)
}