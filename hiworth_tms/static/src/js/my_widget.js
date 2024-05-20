openerp.hiworth_tms = function (instance) {
    instance.web.list.columns.add('field.vehicle_documents_widget', 'instance.hiworth_tms.vehicle_documents_widget');
    instance.hiworth_tms.vehicle_documents_widget = instance.web.list.Column.extend({
        _format: function (row_data, options) {
            res = this._super.apply(this, arguments);
            var pollution_date = res;
            var date = new Date();
            // var date = today.getFullYear()+'-'+(today.getMonth()+1)+'-'+today.getDate();
            // var date = new Date('4-1-2015');
            var d = date.getDate();
            var m = date.getMonth() + 1;
            var y = date.getFullYear();

            var dateString = y + '-' + (m <= 9 ? '0' + m : m) + '-' +(d <= 9 ? '0' + d : d);
            var dateString1 = (d <= 9 ? '0' + d : d) + '-' + (m <= 9 ? '0' + m : m) + '-' + y;

            var date_new = new Date(pollution_date);
            var d1 = date_new.getDate();
            var m1 = date_new.getMonth() + 1;
            var y1 = date_new.getFullYear();
            var dateString2 = (d1 <= 9 ? '0' + d1 : d1) + '-' + (m1 <= 9 ? '0' + m1 : m1) + '-' + y1;

            if (pollution_date != ''){
                if (dateString1 == dateString2){
                    return "<font color='#008000'>"+(dateString2)+"</font>";
                }
                if (dateString1 != dateString2){
                    return "<font color='#000000'>"+(dateString2)+"</font>";
                }
            }
            return res
        }
    });

    instance.web.list.columns.add('field.road_tax_date_widget', 'instance.hiworth_tms.road_tax_date_widget');
    instance.hiworth_tms.road_tax_date_widget = instance.web.list.Column.extend({
        _format: function (row_data, options) {
            res = this._super.apply(this, arguments);
            var road_tax_date = res;
            var date = new Date();
            // var date = today.getFullYear()+'-'+(today.getMonth()+1)+'-'+today.getDate();
            // var date = new Date('4-1-2015');
            var d = date.getDate();
            var m = date.getMonth() + 1;
            var y = date.getFullYear();

            var dateString = y + '-' + (m <= 9 ? '0' + m : m) + '-' +(d <= 9 ? '0' + d : d);
            var dateString1 = (d <= 9 ? '0' + d : d) + '-' + (m <= 9 ? '0' + m : m) + '-' + y;

            var date_new = new Date(road_tax_date);
            var d1 = date_new.getDate();
            var m1 = date_new.getMonth() + 1;
            var y1 = date_new.getFullYear();
            var dateString2 = (d1 <= 9 ? '0' + d1 : d1) + '-' + (m1 <= 9 ? '0' + m1 : m1) + '-' + y1;

            if (road_tax_date != ''){
                if (dateString1 == dateString2){
                    return "<font color='#008000'>"+(dateString2)+"</font>";
                }
                if (dateString1 != dateString2){
                    return "<font color='#000000'>"+(dateString2)+"</font>";
                }
            }
            return res
        }
    });

    instance.web.list.columns.add('field.fitness_date_widget', 'instance.hiworth_tms.fitness_date_widget');
    instance.hiworth_tms.fitness_date_widget = instance.web.list.Column.extend({
        _format: function (row_data, options) {
            res = this._super.apply(this, arguments);
            var fitness_date = res;
            var date = new Date();
            // var date = today.getFullYear()+'-'+(today.getMonth()+1)+'-'+today.getDate();
            // var date = new Date('4-1-2015');
            var d = date.getDate();
            var m = date.getMonth() + 1;
            var y = date.getFullYear();

            var dateString = y + '-' + (m <= 9 ? '0' + m : m) + '-' +(d <= 9 ? '0' + d : d);
            var dateString1 = (d <= 9 ? '0' + d : d) + '-' + (m <= 9 ? '0' + m : m) + '-' + y;

            var date_new = new Date(fitness_date);
            var d1 = date_new.getDate();
            var m1 = date_new.getMonth() + 1;
            var y1 = date_new.getFullYear();
            var dateString2 = (d1 <= 9 ? '0' + d1 : d1) + '-' + (m1 <= 9 ? '0' + m1 : m1) + '-' + y1;

            if (fitness_date != ''){
                if (dateString1 == dateString2){
                    return "<font color='#008000'>"+(dateString2)+"</font>";
                }
                if (dateString1 != dateString2){
                    return "<font color='#000000'>"+(dateString2)+"</font>";
                }
            }
            return res
        }
    });

    instance.web.list.columns.add('field.insurance_date_widget', 'instance.hiworth_tms.insurance_date_widget');
    instance.hiworth_tms.insurance_date_widget = instance.web.list.Column.extend({
        _format: function (row_data, options) {
            res = this._super.apply(this, arguments);
            var insurance_date = res;
            var date = new Date();
            // var date = today.getFullYear()+'-'+(today.getMonth()+1)+'-'+today.getDate();
            // var date = new Date('4-1-2015');
            var d = date.getDate();
            var m = date.getMonth() + 1;
            var y = date.getFullYear();

            var dateString = y + '-' + (m <= 9 ? '0' + m : m) + '-' +(d <= 9 ? '0' + d : d);
            var dateString1 = (d <= 9 ? '0' + d : d) + '-' + (m <= 9 ? '0' + m : m) + '-' + y;

            var date_new = new Date(insurance_date);
            var d1 = date_new.getDate();
            var m1 = date_new.getMonth() + 1;
            var y1 = date_new.getFullYear();
            var dateString2 = (d1 <= 9 ? '0' + d1 : d1) + '-' + (m1 <= 9 ? '0' + m1 : m1) + '-' + y1;

            if (insurance_date != ''){
                if (dateString1 == dateString2){
                    return "<font color='#008000'>"+(dateString2)+"</font>";
                }
                if (dateString1 != dateString2){
                    return "<font color='#000000'>"+(dateString2)+"</font>";
                }
            }
            return res
        }
    });
    //
    //here you can add more widgets if you need, as above...
    //
};
