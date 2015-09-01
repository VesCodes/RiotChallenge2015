$(document).ready(function() {
$(document).pjax('a:not(.navbar.logo, .region-switcher li a)', '.container.body'); // pjaxin'

// ___ TYPEAHEAD ___ //
itemData = []
champData = []
$.getJSON( "/static/json/typeahead.json", function(jsonData) {
	$.each(jsonData['items'], function (index, item) {
	  	itemData.push({id: item['id'], name: item['name'], sprite: item['sprite'], spriteX: item['x'], spriteY: item['y']});
	});
	$.each(jsonData['champions'], function (index, champ) {
		champData.push({id: champ['id'], name: champ['name'], key: champ['key'], sprite: champ['sprite'], spriteX: champ['x'], spriteY: champ['y']});
	});

	$('.navbar.search-bar').typeahead({
		minLength: 1,
		hint: false,
		cache: false, // DISABLE IF MAKING CHANGES
		group: [true, "{{group}}"],
		mustSelectItem: true,
		searchOnFocus: true,
	    order: "asc",
	    template: "<div style='background: url(/static/images/sprite/{{sprite}}) -{{spriteX}}px -{{spriteY}}px; width: 32px; height: 32px; display: inline-block; border-radius: 4px;'></div> <span>{{name}}</span>",
	    source: {
	    	ITEMS: {
	    		display: ['name'],
	    		data: itemData,
	    		href: '/' + region + '/item/{{id}}'
	    	},
	    	CHAMPIONS: {
	    		display: ['name'],
	    		data: champData,
	    		href: '/' + region + '/champions/#{{key}}'
	    	}
	    },
	    callback: {
			onClickAfter: function (node, a, item, event) {
				$.pjax({url: item.href, container: '.container.body'})
				$('.navbar.search-bar').blur()
			}
	    }
	});
})

// ___ TYPEAHEAD: Custom ENTER helper ___ //
$('.navbar.search-bar').on('keydown', function(e) {
	if (e.keyCode === 13) {
		if (!$(".typeahead-list > li.active")[0]) {
			$('.typeahead-list').find('a:first').trigger('click');
		}
		$(this).blur();
	}
});

});

function itemChart(chartJson) {
$.getJSON(chartJson, function(itemData) {
	if (!itemData['global']) {
		$('.chart').replaceWith("<div style='display: table; width: 100%; height: 100px;'><div style='display: table-cell; vertical-align: middle; text-align: center; font-size: 24px; font-weight: bold;'>NO TIMELINE DATA FOR THIS ITEM</div></div>")
	}

	Chart.types.Line.extend({
	    name: 'LineWithPurchasePoint',
	    initialize: function () {
	        Chart.types.Line.prototype.initialize.apply(this, arguments);
	    },
	    draw: function () {
	        Chart.types.Line.prototype.draw.apply(this, arguments);
	        var point = this.datasets[0].points[3].x
	        var scale = this.scale

	        this.chart.ctx.beginPath();
	        this.chart.ctx.moveTo(point, scale.startPoint + 15);
	        this.chart.ctx.strokeStyle = '#ffffff';
	        this.chart.ctx.lineWidth = 3;
	        this.chart.ctx.lineTo(point, scale.endPoint);
	        this.chart.ctx.stroke();
	        
	        this.chart.ctx.textAlign = 'center';
	        this.chart.ctx.font = 'bold 22px Cousine';
	        this.chart.ctx.fillStyle = '#ffffff';
	        this.chart.ctx.fillText('PURCHASE', point, scale.startPoint + 5);
	    }
	});

	var ctx = $('.item-chart .chart').get(0).getContext('2d');

	var chartData = {
		labels: itemData['global'].timestamps,
		datasets: [
			{
				label: 'Gold per 5',
				data: itemData['global'].goldData,
				strokeColor: 'rgba(224, 224, 29, 1)',
				fillColor: 'rgba(255,255,255, 0)',
				pointColor: 'rgba(238, 238, 64, 1)',
				pointStrokeColor: 'rgba(18, 18, 19, 1)'
			},
			{
				label: 'Creeps per Min',
				data: itemData['global'].creepsData,
				strokeColor: 'rgba(29, 224, 211, 1)',
				fillColor: 'rgba(255,255,255, 0)',
				pointColor: 'rgba(63, 227, 216, 1)',
				pointStrokeColor: 'rgba(18, 18, 19, 1)'
			},
			{
				label: 'KDA',
				data: itemData['global'].kdaData,
				strokeColor: 'rgba(224, 29, 29, 1)',
				fillColor: 'rgba(255,255,255, 0)',
				pointColor: 'rgba(255, 60, 60, 1)',
				pointStrokeColor: 'rgba(18, 18, 19, 1)'
			}
		]
	};

	var itemChart = new Chart(ctx).LineWithPurchasePoint(chartData, {
		bezierCurve : false,
		responsive: true,
		maintainAspectRatio: false,
		scaleFontSize: 13,
		scaleFontColor: '#fff',
		scaleFontFamily: 'Cousine',
		tooltipFontFamily: 'Cousine',
		tooltipTitleFontSize: 16,
		tooltipTitleFontFamily: 'Cousine',
		scaleShowLabels: false,
		scaleShowGridLines : false,
		multiTooltipTemplate: '<%= value %> <%= datasetLabel %>',
		pointDotRadius : 5,
		pointDotStrokeWidth: 1,
		datasetStrokeWidth: 3
	});
	
	// TOGGLES
	oldSet = {0: [], 1: [], 2: []};
	$('.chart-toggles a').click(function() {
		targetset = $(this).data('targetset');
		if ($(this).hasClass('enabled')) {
			$.each(itemChart.datasets[targetset].points, function(point, value) {
				oldSet[targetset].push(value.value);
				value.value = null;
			});
		} else {
			$.each(itemChart.datasets[targetset].points, function(point, value) {
				value.value = oldSet[targetset][point];
			})
		}
		$(this).toggleClass('enabled');
		itemChart.update();
	});

	// FILTER
	$('.champ-filter select').on('change', function() {
		champ = $(this).val();
		newData = [itemData[champ]['goldData'], itemData[champ]['creepsData'], itemData[champ]['kdaData']];

		// replace labels & datasets
		oldSet = {0: [], 1: [], 2: []};
		itemChart.scale.xLabels = itemData[champ]['timestamps']
		$.each(itemChart.datasets, function(setIndex, dataset) {
			$.each(dataset.points, function(point, value) {
				value.value = newData[setIndex][point];
				value.label = itemData[champ]['timestamps'][point]
				oldSet[setIndex].push(value.value);
			})
		});

		// respect toggles states
		$.each($('.chart-toggles a'), function(x, toggle) {
			targetset = $(this).data('targetset');
			if (!$(toggle).hasClass('enabled')) {
				$.each(itemChart.datasets[targetset].points, function(point, value) {
					value.value = null;
				});
			} else {
				$.each(itemChart.datasets[targetset].points, function(point, value) {
					value.value = oldSet[targetset][point];
				});
			}
		});

		itemChart.update();
	});
}).fail(function(){
	$('.chart').replaceWith("<div style='display: table; width: 100%; height: 100px;'><div style='display: table-cell; vertical-align: middle; text-align: center; font-size: 24px; font-weight: bold;'>NO GAME DATA FOR THIS ITEM</div></div>")
});

// ___ ITEM INFO ACCORDION ___ //
$('a.itemBlock-toggle').click(function() {
	block = $('.itemBlock-detailed')
	if (block.hasClass('enabled')) {
		$('.itemBlock-short .toggle-text').html('EXPAND ITEM DETAILS &#x25BE;')
		block.slideUp(337, function() { // 1337 is too slow :(
			block.toggleClass('enabled');
		})
	} else {
		$('.itemBlock-short .toggle-text').html('COLLAPSE ITEM DETAILS &#x25B4;')
		block.slideDown(337, function() {
			block.toggleClass('enabled');
		})
	}
});
}

function tableList() {
	// ___ DATATABLE INIT ___ //
	$('.tablelist').dataTable({
		order: [1, 'desc'],
		aoColumns: [
			{ asSorting: [ "asc", "desc" ] },
			{ asSorting: [ "desc", "asc" ] },
			{ asSorting: [ "desc", "asc" ] },
			{ asSorting: [ "desc", "asc" ] },
			{ asSorting: [ "desc", "asc" ] },
		],
		paging: false,
		searching: false,
		info: false
	});

	// ___ SCROLL TO TARGET ___ //
	$('tbody tr').click(function() {
		$('tr.target').not(this).removeClass('target')
		$(this).toggleClass('target')
		window.location.hash = $(this).attr('id').replace('_', '')
	})

	if (window.location.hash) {
		target = window.location.hash.replace('#', '#_')
		offset = $(target.toLowerCase()).offset().top
		$(target.toLowerCase()).toggleClass('target')
		$(window).scrollTop(offset-61)
	}
}

function tableListPJAX() {
	// ___ SCROLL TO TARGET (PJAX) ___ //
	if (window.location.hash) {
		$(window).scrollTop(offset-61)
	}	
}

function regionSwitcher(currentRegion) {
	$('.region-switcher li.active').click(function(e) {
		currentLoc = window.location.href

		$.each($('.region-switcher li:not(li.active)'), function() {
			targetRegion = $(this).data('region')
			$('a', this).attr('href', currentLoc.replace('/' + currentRegion + '/', '/' + targetRegion + '/'))
			if (!$(this).hasClass('shown'))
				$(this).addClass('shown')
			else
				$(this).removeClass('shown')
		})
		
		$(this).toggleClass('dropped');
		e.stopPropagation();
	})
	$('html').click(function() {
		$('.region-switcher li').each(function() {
			if ($(this).hasClass('dropped'))
				$(this).removeClass('dropped');
			if ($(this).hasClass('shown'))
				$(this).removeClass('shown');
		});
	});
}