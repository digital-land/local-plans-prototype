/*global L createElementWithClasses */

(function(L) {

  const TogglableDisplayGroup = L.FeatureGroup.extend({

    options: {
      _displayOnOwn: false,
      _displayedStr: "Switch off",
      _notDisplayedStr: "Switch on"
    },

    _displayed: false,

    isDisplayed: function() { return this._displayed },
    toggleDisplayed: function() {
      // check if _linkedMap is set
      if (this._displayed) {
        this._linkedMap.removeLayer(this);
        this._setControlState();
      } else {
        this._linkedMap.addLayer(this);
        this._setControlState("visible");
      }
      this._displayed = !this._displayed;
    },


    _addControlToParent: function(parent) {
      parent.appendChild(this._controlElement);
      this._addControlEventHandlers();
    },
    _addControlEventHandlers: function() {
      // using arrow function negates need to make reference to 'this' obj
      // instead of pointing to context scope 'this' will point to what is outside this
      // declaration. In this case this = layer object
      this._controlElement.addEventListener("click", () => {
        this.toggleDisplayed();
      });
    },
    _createControlElement: function() {
      const control = createElementWithClasses("li", "layer-toggle");
      const button = document.createElement("button");
      button.textContent = this.options._notDisplayedStr;
      control.appendChild(button);
      this._controlElement = control;
    },
    _getControlElement: function() {
      return this._controlElement;
    },
    _setControlState: function(state) {
      if (state === "visible") {
        this._controlElement.classList.add("displayed");
        this._setControlBtnText(this.options._displayedStr);
      } else {
        this._controlElement.classList.remove("displayed");
        this._setControlBtnText(this.options._notDisplayedStr);
      }
    },
    _setControlBtnText: function(text) {
      const button = this._controlElement.querySelector("button");
      button.textContent = text;
    },


    _setMap: function(map) {
      this._linkedMap = map;
    },


    initialize: function(map, visible, opts) {
      this._setMap(map);
      L.setOptions(this, opts);
      L.FeatureGroup.prototype.initialize.call(this, map);

      this._createControlElement();

      if (visible) { this.toggleDisplayed() }
    }
  });

  window.TogglableDisplayGroup = TogglableDisplayGroup;
}(L));
