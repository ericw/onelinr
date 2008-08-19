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
      if(self.onelinerText.val() !== "" && !self.posting) {
        self.posting = true;
        $.post('/'+self.channel, {value:self.onelinerText.val(),key:$('#key').val()},function(data) {
          self.displayOneliner(data);
          self.posted_oneliner_ids.push(data.post_id);
          self.onelinerText.val("").focus();
          self.posting = false;
        },'json');
      }
      return false;
    });

    setInterval(function() {
      $.getJSON('/'+self.channel+'/latest',{from_id: self.lastOnelinerId}, function(oneliners) {
        oneliners = oneliners.reverse();
        $.each(oneliners,function() {
          if ($.inArray(this.post_id,self.posted_oneliner_ids) === -1) {
            self.displayOneliner(this);
            if(window.fluid) {
              window.fluid.showGrowlNotification({
                  title: "New Onelinr in " + self.channel, 
                  description: this.text.replace(/(<([^>]+)>)/gi, ""), 
                  priority: 1, 
                  sticky: false,
                  identifier: "onelinr",
                  onclick: function() {}
              });              
            }
          }
        });
        // set lastOnelinerId to the last id fetched
        if(oneliners.length > 0) {
          self.lastOnelinerId = oneliners[oneliners.length-1].post_id;
        }
      });
    },4000);

    // unread count for fluid
    if(window.fluid) {
      this.unread = 0;
      $(window).blur(function() {
        self.countUnread = true;
      })
      $(window).focus(function() {
        self.countUnread = false;
        self.unread = 0;
        window.fluid.dockBadge = null;
      })      
    }

  },
  displayOneliner: function(oneliner) {
    $('<li id="oneliner-'+oneliner.post_id+'"><span class="handle">'+ oneliner.handle +'</span> '+oneliner.text+' <a href="/'+this.channel+'#oneliner-'+oneliner.post_id+'" class="permalink" title="Permalink for this oneliner">#</a></li>')
      .prependTo($('#oneliners'))
      .hide()
      .fadeIn();
    if(window.fluid && this.countUnread) {
      this.unread++;
      window.fluid.dockBadge = this.unread;
    }
  }
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
  if ($('#oneliners').length > 0) {
    new OnelinerManager($('#current_channel').html());
  }
});

$(function() {
  $("#handle-page").each(function() {
    var handle = $("#handle")[0];
    handle.focus();
    handle.select();
  });
})