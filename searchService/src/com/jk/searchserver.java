package com.jk;

import java.io.BufferedInputStream;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.logging.LogManager;
import java.util.logging.Logger;

import com.mongodb.BasicDBObject;
import com.mongodb.DB;
import com.mongodb.DBCollection;
import com.mongodb.DBCursor;
import com.mongodb.DBObject;
import com.mongodb.MongoClient;
import com.mongodb.MongoCredential;
import com.mongodb.ServerAddress;

import org.apache.commons.cli.BasicParser;
import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;
import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.document.StringField;
import org.apache.lucene.document.TextField;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.index.Term;
import org.apache.lucene.index.IndexWriterConfig.OpenMode;
import org.apache.lucene.queryparser.classic.MultiFieldQueryParser;
import org.apache.lucene.search.BooleanClause;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.ScoreDoc;
import org.apache.lucene.search.TopDocs;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.util.Version;
import org.apache.thrift.TException;
import org.apache.thrift.server.TServer;
import org.apache.thrift.server.TThreadPoolServer;
import org.apache.thrift.transport.TServerSocket;
import org.apache.thrift.transport.TServerTransport;
import org.bson.types.ObjectId;
import org.json.JSONObject;
import org.wltea.analyzer.cfg.DefaultConfig;
import org.wltea.analyzer.dic.Dictionary;
import org.wltea.analyzer.lucene.IKAnalyzer;

public class searchserver {

	/**
	 * @param args
	 */
	static JSONObject PARAMS;
	static Logger logger;

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		String CFG_DIR = "/home/jkiris/dav/self.cfg";
		
		CommandLineParser parser = new BasicParser();  
		Options options = new Options();  
		options.addOption("h", "help", false, "help");  
		options.addOption("f", "file", true, "Config File");  
		// Parse the program arguments  
		CommandLine commandLine;
		try {
			commandLine = parser.parse( options, args );
			if( commandLine.hasOption('h') ) {  
				System.out.println( "Help Message"); 
			    System.exit(0);  
			}  
			if( commandLine.hasOption('f') ) {  
				CFG_DIR = commandLine.getOptionValue('f'); 
			} 
		} catch (ParseException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}  		   		
		
		try {  
			StringBuffer cfg = new StringBuffer();
			try {					
				String line = null ;
				BufferedReader br = new BufferedReader(new FileReader(new File(CFG_DIR)));
				while( (line = br.readLine())!= null ){
					cfg.append(line);
				}
				PARAMS = new JSONObject(cfg.toString());
			}catch (Exception e) {
				System.exit(1);
			}
			if(PARAMS.length() == 0){
				System.exit(1);
			}			
			LogManager lm = LogManager.getLogManager(); 
			try{ 
				InputStream in = new FileInputStream(
						new File(((JSONObject) PARAMS.get("logger")).getString("java"))); 
				BufferedInputStream bin = new BufferedInputStream(in); 
				lm.readConfiguration(bin); 
				logger = Logger.getLogger("thrift");
			}catch (Exception e) {  
				System.exit(1);
			} 
			
			int port = ((JSONObject) searchserver.PARAMS.get("search")).getInt("port");
			searchHandler handler = new searchHandler();
			Search.Processor<searchHandler> processor = new Search.Processor<searchHandler>(handler);
			handler.initSearch();
			TServerTransport serverTransport = new TServerSocket(port);
		    TServer server = new TThreadPoolServer(new TThreadPoolServer.Args(serverTransport).processor(processor)); 
			logger.info("Starting server on port " + port + "...");  
			server.serve();  
		} catch (Exception e) {  
			e.printStackTrace();  
		}
	}
}
	
class searchHandler implements Search.Iface {  	
	static String dir;
	static Analyzer analyzer ;
	static Directory directory ;
	static IndexReader reader ;
	static DB db_primary;
	
	public void initSearch() throws Exception{
		dir = ((JSONObject) searchserver.PARAMS.get("search")).getString("dir");
		analyzer = new IKAnalyzer(true);
		try{
			directory = FSDirectory.open(new File(dir));
			reader = DirectoryReader.open(directory);
		}catch(Exception e){
			e.printStackTrace();
		}
		try {
			((JSONObject) searchserver.PARAMS.get("db_local")).getString("ip");
			String db_primary_ip = ((JSONObject) searchserver.PARAMS.get("db_primary")).getString("ip");
			((JSONObject) searchserver.PARAMS.get("db_local")).getString("username");
			((JSONObject) searchserver.PARAMS.get("db_local")).getString("password");
			String db_primary_uname = ((JSONObject) searchserver.PARAMS.get("db_primary")).getString("username");
			String db_primary_pwd = ((JSONObject) searchserver.PARAMS.get("db_primary")).getString("password");

			MongoCredential credential = MongoCredential.createCredential(db_primary_uname, "feed", db_primary_pwd.toCharArray());
			MongoClient mongo_primary = new MongoClient(new ServerAddress(db_primary_ip, 27017), Arrays.asList(credential));
			db_primary = mongo_primary.getDB("feed");
		} catch (Exception e) {
			// TODO Auto-generated catch block
			searchserver.logger.info(e.toString());
		}
		Dictionary.initial(DefaultConfig.getInstance()); 
	}
	@Override
	public Result search(String wd, int start, int length) throws TException {
		// TODO Auto-generated method stub
		String query = wd.replaceAll("[\\+\\-\\*\\%\\.\\:\\@\\#\\&\\|\\_\\(\\)\\{\\}]", " ");
		String[] fields = {"title", "des",};
		BooleanClause.Occur[] flags = {BooleanClause.Occur.SHOULD,
		                BooleanClause.Occur.SHOULD};
		Query q;
		try {
			q = MultiFieldQueryParser.parse(query, fields, flags, analyzer);
			IndexSearcher searcher = new IndexSearcher(reader);
		    TopDocs topDocs = searcher.search(q, start+length);
		    ScoreDoc[] hits = topDocs.scoreDocs;
		    
		    Result res = new Result(true);
		    res.data = new HashMap<String,String>();
		    if(hits.length > start){
			    ArrayList<String> result = new ArrayList<String>();
			    Document d;
			    for(int i=start;i<start+length;++i) {
			    	int docId = hits[i].doc;
			    	d = searcher.doc(docId);
			    	result.add("ObjectId('" + d.get("id") + "')");
			    }
			    res.data.put("searchresult", result.toString());
		    }
		    if(hits.length >= start+length){
			    res.data.put("hasmore", "True");
		    }
		    else
		    	res.data.put("hasmore", "False");
	        return res;
		} catch (Exception e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			searchserver.logger.info(e.toString());
			Result res = new Result(false);
	        res.msg = e.toString();
	        return res;
		}	    
	}
	@Override
	public Result updateSearchIndex() throws TException {
		// TODO Auto-generated method stub
		IndexWriterConfig config = new IndexWriterConfig(Version.LUCENE_CURRENT, analyzer);
		DBCollection feed = db_primary.getCollection("item");
		BasicDBObject query = new BasicDBObject();
		String latest = "" ;
		try{
			IndexSearcher searcher = new IndexSearcher(reader);
			latest = searcher.doc(reader.maxDoc()-1).get("id");

			ObjectId id = new ObjectId(latest);
			query.put("_id", new BasicDBObject("$gt",id));
			config.setOpenMode(OpenMode.APPEND);
		}catch(Exception e){
			config.setOpenMode(OpenMode.CREATE);
		}
		searchserver.logger.info("updating index ......");
		IndexWriter writer;
		try {
			writer = new IndexWriter(directory, config);
			DBCursor cursor = feed.find(query);
	        Document doc;
	        DBObject u;
	        while(cursor.hasNext()){
	        	u = cursor.next();
	        	doc = new Document();
		        try{
		        	doc.add(new StringField("id", u.get("_id").toString(), Field.Store.YES));
		        	doc.add(new TextField("title", (String) u.get("title"), Field.Store.YES));
		        	doc.add(new TextField("des", (String) u.get("des"), Field.Store.YES));
		        	writer.updateDocument(new Term("id", u.get("_id").toString()), doc);
		        }catch(IOException e){
		        	e.printStackTrace();
		        }
	        	latest = u.get("_id").toString();
	        }
	        writer.close();	        
	        initSearch();	  
	        searchserver.logger.info("update index finished");
	        Result res = new Result(true);
	        res.data = new HashMap<String, String>();
	        res.data.put("latest", latest);
	        return res;
		} catch (Exception e1) {
			// TODO Auto-generated catch block
			searchserver.logger.info(e1.toString());
			Result res = new Result(false);
	        res.msg = e1.toString();
	        return res;
		}
	}  
}  
