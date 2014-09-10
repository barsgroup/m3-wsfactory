/**
 * Created by tim on 10.09.14.
 */
var inProtocolGrid = Ext.getCmp("{{ component.InProtocol_param_grid.client_id }}");
setGridCellEditor(inProtocolGrid, "valueEditor");
submitGridStore(win, inProtocolGrid, "InProtocol");

var inProtocolField = Ext.getCmp("{{ component.InProtocol_field.client_id }}");
inProtocolField.on("change", function (cmp, value) {
  var currentValue = this.getStore().baseParams["protocol_code"];
  if (currentValue !== value) {
    this.getStore().setBaseParam("protocol_code", value);
    this.getStore().reload();
  }
}, inProtocolGrid);