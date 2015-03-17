d3.json("/rs/getupre?target=wd", function(error, res) {
	if(res.data){
		var ww = 700;
		var wh = 450;
		var fill = d3.scale.category20();
  		var max = res.data[0].count;
  		var fontsize = d3.scale.linear().range([10, 80]).domain([1, max]);
  		d3.layout.cloud().size([ww, wh])
  			.timeInterval(10)
      		.words( [].map.call(res.data, function(x) {
				return {text: x.name, size: x.count};
      		}))
      		// .rotate(function() { return ~~(Math.random() * 2) * 90; }) //just do not set rotate yourself
      		.font("Impact")
      		.spiral("archimedean")
      		.fontSize(function(d) { return fontsize(d.size); })
      		.on("end", draw)
      		.start();
  		function draw(words) {
    		d3.select("svg.word")
        		.attr("width", ww)
        		.attr("height", wh)
      		.append("g")
        		.attr("transform", "translate("+ww/2+","+wh/2+")")
      		.selectAll("text")
        		.data(words)
      			.enter().append("text")
        		.style("font-size", function(d) { return d.size + "px"; })
        		.style("font-family", function(d) { return d.font; })
        		.style("fill", function(d, i) { return fill(i); })
        		.attr("text-anchor", "middle")
        		.attr("class", "wd")
        		.attr("transform", function(d) {
          			return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";
       		})
        	.text(function(d) { return d.text; })
        	.on("mouseover", function(d){
        		d3.select(this)
        		.style("font-size", function(d) { return 2*d.size + "px"; })
        		.style("fill", "black");
        	})
        	.on("mouseout", function(d, i){
        		d3.select(this)
        		.style("font-size", function(d) { return d.size + "px"; })
        		.style("fill", function(d, i) { return fill(i); });
        	})
        	.on("click", function(d){
        		var _searchparams = {'wd':d.text};
				window.open("/rs/search?" + $.param( _searchparams, true ));
			});
  		}
	}
});
d3.json("/rs/getupre?target=source", function(error, res) {
	if (res.data){
		var sw = 700;
		var sh = 250;
		var barPadding = 1;
		var sourcesvg = d3.select("svg.source")
			.attr("width",sw)
			.attr("height",sh+50);
		var xScale = d3.scale.ordinal()
						.domain( d3.range(res.data.length) )
						.rangeRoundBands( [0,sw], 0.05 );
		var yScale = d3.scale.linear()
						.domain( [0, res.data[0].count] )
						.range( [0, sh] );
		var groups = sourcesvg.selectAll("g")
			.data(res.data)
			.enter()
			.append("g");
		var rects = groups.data(res.data)
			.append("rect")
			.attr({
				"x": function(d,i){ return xScale(i); },
				"y": function(d){ return sh-yScale(d.count); },
				"height": function(d){ return yScale(d.count); },
				"width": xScale.rangeBand(),
			})
			.on("click", function(d){
				window.open("/rs/lookclassify?" + $.param({'source':[d.name,]}));
			});
		var texts = groups.data(res.data)
			.append("text")
			.text( function(d){ return d.name; } )
			.attr({
				x: function(d,i){ return xScale(i)+6; },
				y: function(d){ return sh+11; },
				"fill": "black",
				"font-size": "15px",
				"font-family": "sans-serif"
			})
			.attr("transform", function(d,i) { 
				return "rotate(20,"+(xScale(i)+6)+","+(sh+11)+")"; 
			})			;
	}
});

d3.json("/rs/getupre?target=category", function(error, res) {
	if(res.data){
		var tw = 600;
		var th = 600;
		var iR = tw/7;
		var oR = tw/4;
		var categorysvg = d3.select("svg.category")
			.attr("width",tw)
			.attr("height",th);
		var pie = d3.layout.pie()
			.sort(null)
			.value(function(d) { return d.count; });
		var color = d3.scale.category10();
		var arc = d3.svg.arc()
						.innerRadius( iR )
						.outerRadius( oR );
		var sum = d3.sum([].map.call(res.data, function(x) {
			 return x.count; }));
		var tip = categorysvg.append("g");
		tip.append("rect")
			.attr({
				x: 100,
				y: 20,
				"height": 20,
				"width": 20,
				"fill": "white",
				"id": "tiprect",
			});
		tip.append("text")
			.text("all: "+sum+"/"+sum)
			.attr({
				x: 125,
				y: 35,
				"fill": "black",
				"id": "tiptext",
				"font-size": "15px",
			});
		var arcs = categorysvg.selectAll("g.pie")
			.data( pie(res.data) )
			.enter()
			.append("g")
			.attr("class", "pie")
			.attr("transform", "translate(" + tw/2 + "," + th/2 + ")");
		arcs.append("path")
			.attr("fill", function(d, i){
				return color(i);
			})
			.attr("d", arc)
			.on("mouseover", function(d, i){
				tip.select("#tiprect")
					.attr("fill", color(i));
				tip.select("#tiptext")
					.text( d.data.name+": "+d.value+"/"+sum);
			})
			.on("mouseout", function(d, i){
				tip.select("#tiprect")
					.attr("fill", "white");
				tip.select("#tiptext")
					.text("all: "+sum+"/"+sum);
			})
			.on("click", function(d){
				window.open("/rs/lookclassify?" + $.param({'category':[d.data.name,]}));
			});
		var startAngle = -90;
		arcs.append("text")
			.text(function(d){
				if(d.value/sum > 10/360)
					return d.data.name;
			})
			.attr({
				x: oR+2,
				y: 0,
				"fill": "black",
				"font-size": "15px",
				"transform": function(d){
					var currAngle = startAngle + 180*d.value/sum;
					startAngle = startAngle + 360*d.value/sum;
					return "rotate("+currAngle+")";}
			});
	}
	
});