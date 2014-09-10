/**
 * Created by tim on 08.09.14.
 */

{% include "ui-js/column-editor.js" %}

var grid = Ext.getCmp("{{ component.param_grid.client_id }}");
setGridCellEditor(grid, "valueEditor");
submitGridStore(win, grid);

var moduleField = Ext.getCmp("{{ component.module_field.client_id }}");
moduleField.on("change", function (cmp, value) {
  var currentValue = this.getStore().baseParams["module_code"];
  if (currentValue !== value) {
    this.getStore().setBaseParam("module_code", value);
    this.getStore().reload();
  }
}, grid);