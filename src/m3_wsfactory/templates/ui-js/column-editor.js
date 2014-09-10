/**
 * Created by tim on 08.09.14.
 */

var setGridCellEditor = function (grid, editorField) {
  var cellEditor = {};

  editorField = editorField || "valueEditor";
  grid.getColumnModel().getCellEditor = function (colIndex, rowIndex) {
    return cellEditor[rowIndex]
  };
  var store = grid.getStore();
  store.on('load', function () {
    this.each(function (record) {
      var editor = smart_eval(record.get(editorField));
      if (editor) {
        cellEditor[this.indexOf(record)] = new Ext.grid.GridEditor(editor)
      }
    }, this);
  })

};

var valueRenderer = function (value, metaData, record) {
  var valueType = record.get("valueType");
  var display = value;
  if (valueType === "password"){
    display = new Array(value.toString().length + 1).join("*")
  }
  return display;
};

var submitGridStore  = function (winObj, grid, prefix) {
  prefix = prefix ? prefix + "." : "";
  winObj.on("beforesubmit", function (submit) {
    var params = {paramNames: []};
    this.getStore().each(function (record) {
      this[prefix + record.get("key")] = record.get("value");
      this.paramNames.push(prefix + record.get("key"));
    }, params);
    params.paramNames = params.paramNames.join(",");
    if (submit.params.paramNames) {
      params.paramNames = [params.paramNames, submit.params.paramNames].join(",")
    }
    Ext.apply(submit.params, params);
  }.bind(grid));

  winObj.on("show", function () {
    this.getEl().mask();
  }.bind(winObj));
  
  grid.getStore().on("load", function () {
    winObj.getEl().unmask();
  }, winObj);

};

