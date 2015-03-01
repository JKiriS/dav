# -*- coding: utf-8 -*-
import jpype 

jvmpath = jpype.getDefaultJVMPath()  
jpype.startJVM(jvmpath, "-ea", "-Djava.class.path=test.jar")  
ST = jpype.JClass("test.test")  
#gt = jpype.JPackage("test").gephitest() 
#print ST.search(u"百度", u"index")
print ST.createIndex(u"index", u'new')
jpype.shutdownJVM(); 
