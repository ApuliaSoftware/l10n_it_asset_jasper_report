# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Apulia Software S.r.l. (<info@apuliasoftware.it>)
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from osv import fields, osv
from tools.translate import _
import openerp.addons.decimal_precision as dp


class asset_journal_wz(osv.osv_memory):

    _name = "asset.journal.wz"
    _description = "Parametri Stampa Libro Cespiti"

    _columns = {'date': fields.date('Print Date', required=True),
                'fiscal_year': fields.many2one('account.fiscalyear',
                                               'Period to Print',
                                               required=True),
                'asset_type': fields.selection(
                    (('M', 'Material asset'),
                     ('I', 'Intangible asset'),
                     ('P', 'Capital gain'),
                     ('A', 'All')),
                    'Type'),
                'cat_id': fields.many2one('account.asset.category',
                                          'Asset Category'),
                'first_page_number': fields.float('From Page'),
                'not_moved_too': fields.boolean('Assets without Moves'),
                }

    _defaults = {'asset_type': 'A'}

    def print_asset_journal(self, cr, uid, ids, context=None):
        asset_obj = self.pool['account.asset.asset']
        param = self.browse(cr, uid, ids[0])
        filters = []
        data = {}
        if param.cat_id:
            filters.append(('category_id', '=', param.cat_id.id))
        if param.asset_type != 'A':
            cat_ids = self.pool.get('account.asset.category').search(
                cr, uid, [('asset_type', '=', param.asset_type)])
            if cat_ids:
                filters.append(('category_id', 'in', cat_ids))
        asset_ids = asset_obj.search(cr, uid, filters)
        if asset_ids:
            ok = self.pool.get('asset.journal.temp').crea_temp(cr, uid,
                                                               asset_ids,
                                                               param)
            if ok:
                return self._print_report(cr, uid, ids, data, param,
                                          context=context)
            else:
                raise osv.except_osv(_('Error'),
                                     _("No data to print"))
        else:
            raise osv.except_osv(_('Error'),
                                 _("No data to print"))
        return {'type': 'ir.actions.act_window_close'}

    def _print_report(self, cr, uid, ids, data, parametri, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = {}
        return {'type': 'ir.actions.report.xml',
                'report_name': 'asset_journal',
                'datas': data,
                }


class asset_journal_temp(osv.osv_memory):

    _name = "asset.journal.temp"
    _description = "Tmp Asset Journal"

    _columns = {'date': fields.date('Print Date'),
                'fiscal_year': fields.many2one('account.fiscalyear',
                                               'Period to Print'),
                'asset_type': fields.selection(
                    (('M', 'Material asset'),
                     ('I', 'Intangible asset'),
                     ('P', 'Capital gain'),
                     ('A', 'All')),
                    'Type Asset'),
                'cat_id': fields.many2one('account.asset.category',
                                          'Asset Category'),
                'first_page_number': fields.float('From Page'),
                'not_moved_too': fields.boolean('Assets Without Moves'),
                'asset_id': fields.many2one('account.asset.asset', 'Asset'),
                'category_id': fields.many2one('account.asset.category',
                                               'Asset Category'),
                'deductibility': fields.float(
                    'Perc. di deducibilita',
                    digits_compute=dp.get_precision('Account')),
                'purchase_date': fields.date('Purchase Date'),
                'purchase_value': fields.float('Gross Value'),
                'value_residual': fields.float('Residual Value'),
                'type_amortization': fields.selection(
                    (('O', 'ordinary'),
                     ('F', 'firs year reduction'),
                     ('A', 'advance'),
                     ('R', 'reduced'),
                     ('P', 'personal')),
                    'Tipo Ammortamento'),
                'perc_ammortization': fields.float(
                    'Percentage Amortization',
                    digits_compute=dp.get_precision('Account')),
                'depreciated_value': fields.float(
                    'Amount Already Depreciated'),
                'amount': fields.float(
                    'Current Depreciation',
                    digits_compute=dp.get_precision('Account')),
                'remaining_value': fields.float(
                    'Next Period Depreciation',
                    digits_compute=dp.get_precision('Account')),
                'sale_date': fields.date('Sale Date'),
                }

    def _pulisci(self, cr, uid, context=None):
        ids = self.search(cr, uid, [])
        self.unlink(cr, uid, ids, context)
        return True

    def crea_temp(self, cr, uid, ids, param, context=None):
        asset_obj = self.pool.get('account.asset.asset')
        asset_dep_lineobj = self.pool.get('account.asset.depreciation.line')
        invoice_lineobj = self.pool.get('account.invoice.line')
        ok = self._pulisci(cr, uid, context)
        ok = False
        if not ids:
            return False
        for asset in asset_obj.browse(cr, uid, ids):
            id_line_dep = asset_dep_lineobj.search(cr, uid, [
                ('asset_id', '=', asset.id),
                ('fiscal_year', '=', param.fiscal_year.id)])
            id_line_invoice = invoice_lineobj.search(cr, uid, [
                ('asset_id', '=', asset.id),
                ('date_invoice', '>=', param.fiscal_year.date_start),
                ('date_invoice', '<=', param.fiscal_year.date_stop)])
            if not id_line_dep and not id_line_invoice \
                    and not param.not_moved_too:
                print_asset = False
            if not id_line_dep and not id_line_invoice \
                    and param.not_moved_too:
                print_asset = True
            if id_line_dep or id_line_invoice:
                print_asset = True
            if print_asset:
                vals = {}
                if id_line_dep:
                    line_dep = asset_dep_lineobj.browse(cr, uid,
                                                        id_line_dep[0])
                    vals = {
                        'date': param.date,
                        'fiscal_year': param.fiscal_year.id,
                        'asset_type': param.asset_type,
                        'cat_id': param.cat_id.id,
                        'first_page_number': param.first_page_number,
                        'not_moved_too': param.not_moved_too,
                        'asset_id': asset.id,
                        'category_id': asset.category_id.id,
                        'deductibility': asset.deductibility,
                        'purchase_date': asset.purchase_date,
                        'purchase_value': asset.purchase_value,
                        'value_residual': asset.value_residual,
                        'type_amortization': line_dep.type_amortization,
                        'perc_ammortization': line_dep.perc_ammortization,
                        'depreciated_value': line_dep.depreciated_value,
                        'amount': line_dep.amount,
                        'remaining_value': line_dep.remaining_value,
                        'sale_date': asset.sale_date,
                    }
                else:
                    line_dep = False
                    if asset.remaining_value <= 0.0:
                        # cespite completamente ammortizzato
                        if asset.type_amortization == 'O':
                            perc = asset.ordinary_amortization
                        if asset.type_amortization == 'R':
                            perc = asset.amortization_reduced
                        if asset.type_amortization == 'A':
                            perc = asset.early_ammortization
                        if asset.type_amortization == 'P':
                            perc = asset.personal_ammortization
                        vals = {
                            'date': param.date,
                            'fiscal_year': param.fiscal_year.id,
                            'asset_type': param.asset_type,
                            'cat_id': param.cat_id.id,
                            'first_page_number': param.first_page_number,
                            'not_moved_too': param.not_moved_too,
                            'asset_id': asset.id,
                            'category_id': asset.category_id.id,
                            'deductibility': asset.deductibility,
                            'purchase_date': asset.purchase_date,
                            'purchase_value': asset.purchase_value,
                            'value_residual': asset.value_residual,
                            'type_amortization': asset.type_amortization,
                            'perc_ammortization': perc,
                            'depreciated_value': asset.value_residual,
                            'amount': 0.0,
                            'remaining_value': 0.0,
                            'sale_date': asset.sale_date,
                        }
                    else:
                        if asset.remaining_value > 0.0 \
                                and not asset.sale_date:
                            raise osv.except_osv(
                                _('Error'),
                                _("Amortization not calculated for period \
%s" % (asset.name)))
                        else:
                            perc=0.0
                            if asset.type_amortization == 'O':
                                perc = asset.ordinary_amortization
                            if asset.type_amortization == 'R':
                                perc = asset.amortization_reduced
                            if asset.type_amortization == 'A':
                                perc = asset.early_ammortization
                            if asset.type_amortization == 'P':
                                perc = asset.personal_ammortization
                            vals = {
                                'date': param.date,
                                'fiscal_year': param.fiscal_year.id,
                                'asset_type': param.asset_type,
                                'cat_id': param.cat_id.id,
                                'first_page_number': param.first_page_number,
                                'not_moved_too': param.not_moved_too,
                                'asset_id': asset.id,
                                'category_id': asset.category_id.id,
                                'deductibility': asset.deductibility,
                                'purchase_date': asset.purchase_date,
                                'purchase_value': asset.purchase_value,
                                'value_residual': asset.value_residual,
                                'type_amortization': asset.type_amortization,
                                'perc_ammortization': perc,
                                'depreciated_value': 0.0,
                                'amount': 0.0,
                                'remaining_value': 0.0,
                                'sale_date': asset.sale_date,
                            }
                if vals:
                    self.create(cr, uid, vals)
                    ok = True
        return ok
