struct Result {
  1: bool success = true,
  2: optional string msg,
  3: optional map<string,string> data
}

exception FileError {
  1: string who
}

exception DataError {
  1: string who
}