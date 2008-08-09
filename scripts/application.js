var Utils = {
  Class: function() {
    return function() {
      this.initialize.apply(this, arguments);
    };
  },
  bind: function(scope, fn) {
    return function() {
      fn.apply(scope, arguments);
    };
  },
  stop: function(e) { e.preventDefault && e.preventDefault(); return false; },
  noop: function() { return this; } // identity func and terminator for our namespace
};

var OnelinerManager = Utils.Class();
OnelinerManager.prototype = {
  initialize: function(channel){
    this.channel = channel;
    this.posted_oneliner_ids = new Array();
    if($('#oneliners li:first').length > 0) {
      this.lastOnelinerId = $('#oneliners li:first').attr('id').substring(9); //state of which latest oneliner id
    } else {
      this.lastOnelinerId = 0;
    }
    this.onelinerText = $('#oneliner_value');
    this.onelinerText.val("");
    this.onelinerText[0].focus();
    var self = this;
    $('#oneliner-form').bind('submit', function(ev) {
      $.post('/'+self.channel, {value:self.onelinerText.val(),key:$('#key').val()},function(data) {
        console.log(data)
        self.displayOneliner(data);
        self.posted_oneliner_ids.push(data.post_id);
        self.onelinerText.val("").focus();
      },'json');
      return false;
    });

    setInterval(function() {
      $.getJSON('/'+self.channel+'/latest',{from_id: self.lastOnelinerId}, function(oneliners) {
        oneliners = oneliners.reverse();
        console.log(oneliners)
        $.each(oneliners,function() {
          if ($.inArray(this.post_id,self.posted_oneliner_ids) === -1) {
            self.displayOneliner(this);
          }
        });
        // set lastOnelinerId to the last id fetched
        if(oneliners.length > 0) {
          self.lastOnelinerId = oneliners[oneliners.length-1].post_id;
        }
      });
    },4000);
  },
  displayOneliner: function(oneliner) {
    $('<li id="oneliner-'+oneliner.post_id+'">'+oneliner.text+' <a href="/'+this.channel+'#oneliner-'+oneliner.post_id+'" class="permalink" title="Permalink for this oneliner">#</a></li>')
      .prependTo($('#oneliners'))
      .hide()
      .fadeIn();
  },
};

// var ChannelCustomizr = Class.create();
// ChannelCustomizr.prototype = {
//   initialize:function(){
//     //this.color_trigger = $$("#text-color span.value").first();
//     //this.background_trigger = $$("#background span.value").first();
//     this.color_trigger = $("text-color-value");
//     new Control.ColorPicker(this.color_trigger, { "swatch" : "text-color-value",onUpdate: function () {
//       var chan = $('channel');
//       chan.style.backgroundColor = "#"+$("text-color-value").value;
//       //bg input rgb value ljusare an color, dvs hex to rgb -> rgbtohsl -> +20 -> hsltorgb
//     } });
//     // Event.observe(this.color_trigger,'click',function() {
//     //   alert('df');
//     // })
//   }
// }

/* attach observers */
$(function(){
  if ($('#oneliners').length > 0 && (current_channel = $('#current_channel'))) {
    new OnelinerManager(current_channel.html());
    //var customizr = new ChannelCustomizr();
  }
});
