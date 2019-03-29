(function(L){
  const MHCLGMaps = L.Class.extend({  
    // this is the constructor
    initialize: function (options) {
      if(!options.mapbox_token) {
        console.warn('Must provide Mapbox token');
        return false;
      }
      L.Util.setOptions(this, options);
      return this;
    },

    // these are the default options
    options: {
      maxZoom: 18,
      mapHeight: '800px'
    },

    // this is a public function
    createMap: function(idSelector, options) {
      var options = options || {};
      const map = L.map(idSelector, options);
      this.addTileLayer(map);
      this.setMapContainerHeight(map);
      return map;
    },

    addTileLayer: function(map) {
      L.tileLayer(`https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=${this.options.mapbox_token}`, {
          attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
          maxZoom: this.options.maxZoom,
          id: 'mapbox.streets',
          accessToken: '{{ config.MAPBOX_TOKEN }}'
      }).addTo(map);
    },

    setMapContainerHeight: function(map, value, isRatio) {
      var ratio = value || (2/3);
      // set a default value if none provided are height
      // not set with CSS
      if( !value && !map._container.style.height) {
        map._container.style.height = this.options.mapHeight;
      }
      if( isRatio ) {
        var width = map._container.offsetWidth;
        map._container.style.height = `${width * ratio}px`;
      } else {
        // should I check it is a string?
        map._container.style.height = value;
      }
    }
  });

  window.MHCLGMaps = MHCLGMaps;
}(L));
