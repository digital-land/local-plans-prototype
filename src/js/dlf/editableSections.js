/*global setOptions postJSONRequest postFormDataRequest */


// requires funcs:
// * setOptions
// * postFormDataRequest
// * postJSONRequest
// from helpers.js

// --------------------
// Basic Editable Class
// --------------------
function EditableSection(section, opts) {
  this.section = section;

  // defaults
  this.options = {
    allClickable: false,
    activeClass: "edit-mode"
  };

  // merge user set options with defaults
  setOptions(this, opts);

  this.enterEditMode = () => this.section.classList.add(this.options.activeClass);
  this.exitEditMode = () => this.section.classList.remove(this.options.activeClass);

  if (this.options.allClickable) {
    this.setEditTrigger(this.section);
  } else if (this.options.trigger) {
    this.setEditTrigger(this.options.trigger);
  } else {
    this.setEditTrigger();
  }

}

EditableSection.prototype.setEditTrigger = function (selector) {
  if (selector instanceof Element) {
    this.trigger = this.section;
  } else if (selector) {
    this.trigger = this.section.querySelector(selector);
  } else {
    this.trigger = this.section.querySelector(".request-for-update a");
  }
  this.addEditListener();

  if (this.options.cancel) {
    this.setCancelTrigger(this.options.cancel);
  } else {
    this.setCancelTrigger();
  }
}

EditableSection.prototype.addEditListener = function () {
  const that = this;

  function editHandler(e) {
    e.preventDefault();
    that.enterEditMode();
    that.trigger.removeEventListener("click", editHandler);
  }

  this.editHandler = editHandler;
  this.trigger.addEventListener("click", editHandler);
}

EditableSection.prototype.setCancelTrigger = function (selector) {
  if (selector) {
    this.cancel = this.section.querySelector(selector);
    //this.trigger.addEventListener("click", )
  } else {
    this.cancel = this.section.querySelector(".cancel-btn");
  }
  this.addCancelListener();
}

EditableSection.prototype.addCancelListener = function () {
  const that = this;

  function cancelHandler(e) {
    e.stopPropagation();
    e.preventDefault();
    that.exitEditMode();
    that.trigger.addEventListener("click", that.editHandler);
  }

  this.cancel.addEventListener("click", cancelHandler);
}

EditableSection.prototype.initialiseForm = function (extractDataFunc, succCb, errCb) {
  const form = this.section.querySelector("form");
  this.form = form;

  const that = this;
  form.addEventListener("submit", (e) => {
    e.preventDefault();

    const endpoint = form.action;
    const data = extractDataFunc(form);

    const isVisible = function(el) {
      return el.clientWidth > 0
    }

    const hasNoFormGroupErrors = function() {
      const formGroupErrors = Array.from(form.querySelectorAll(".govuk-form-group--error"));
      if (formGroupErrors.length > 0 && formGroupErrors.some(isVisible)) {
        console.log("something with an error must be visible");
        return false;
      }
      return true;
    }

    if (hasNoFormGroupErrors()) {

      form.classList.add("posting");
      if (form.enctype !== undefined && form.enctype == "multipart/form-data"){
        postFormDataRequest(endpoint, data, function(respData) {
          form.classList.remove("posting");

          that.exitEditMode();
          that.trigger.addEventListener("click", that.editHandler);
          if (succCb && typeof succCb === "function") {
            succCb(respData);
          }
        });
      } else {
        postJSONRequest(endpoint, data, function (respData) {

          // handle the response
          form.classList.remove("posting");
          if (respData["OK"] === 200) {
            that.exitEditMode();
            that.trigger.addEventListener("click", that.editHandler);
            if (succCb && typeof succCb === "function") {
              succCb(respData);
            }
          } else {
            if (errCb && typeof errCb === "function") {
              // to do: handle errors better
              errCb();
            }
          }
        });
      }

    } // end has errors check
  });
};
