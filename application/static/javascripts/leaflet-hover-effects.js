(function(L){
  // helper function
  // takes HEX colour and value (-1.0 to 1.0) to change by
  // positive number lightens
  // negative darkens
  // taken from https://stackoverflow.com/questions/5560248/programmatically-lighten-or-darken-a-hex-color-or-rgb-and-blend-colors
  function shadeColour(color, percent) {   
    var f=parseInt(color.slice(1),16),t=percent<0?0:255,p=percent<0?percent*-1:percent,R=f>>16,G=f>>8&0x00FF,B=f&0x0000FF;
    return "#"+(0x1000000+(Math.round((t-R)*p)+R)*0x10000+(Math.round((t-G)*p)+G)*0x100+(Math.round((t-B)*p)+B)).toString(16).slice(1);
  }

  // augment the L.GeoJSON class
  L.GeoJSON.include({
    // add hover event handlers
    //  darkens polygon colour on mouseover
    //  returns style on mouseout
    _addHoverHandlers: function() {
      const self = this;
      // check _defaultStyle has been set
      if ( !Object.prototype.hasOwnProperty.call(self.options, "_defaultStyle") ) {
        // fail silently
        return self;
      }
      // set event listeners
      self.on('mouseover', function(e) {
        self.setStyle( self.options._hoverStyle );
      });
      self.on('mouseout', function(e) {
        self.setStyle( self.options._defaultStyle );
      });
    
      return self;
    },
    // set the Styles
    //  adds default style and a darkened style
    //  to the layer options
    _setDefaultStyles: function(style, hoverS) {
      this.options._defaultStyle = style;
      const hoverStyle = hoverS || {
        color: shadeColour(style.color, -0.25),
        fillColor: shadeColour(style.fillColor, -0.25),
        fillOpacity: style.fillOpacity + 0.1
      };
      this.options._hoverStyle = hoverStyle;
      // set the inital style
      this.setStyle( style );
      return this;
    }

  });

}(L));


