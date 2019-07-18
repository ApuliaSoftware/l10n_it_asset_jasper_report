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
                'lineap_id': fields.many2one('lineap.asset', 'Linea'),
                'sede_id': fields.many2one('asset.sedi', 'Sede'),
                }

    _defaults = {'asset_type': 'A'}

    def print_asset_journal(self, cr, uid, ids, context=None):
        asset_obj = self.pool['account.asset.asset']
        param = self.browse(cr, uid, ids[0])
        filters = []
        data = {}
        if param.cat_id:
            filters.append(('category_id', '=', param.cat_id.id))
        if param.lineap_id:
            filters.append(('lineap_id', '=', param.lineap_id.id))
        if param.sede_id:
            filters.append(('sede_id', '=', param.sede_id.id))
        if param.asset_type != 'A':
            cat_ids = self.pool.get('account.asset.category').search(
                cr, uid, [('asset_type', '=', param.asset_type)])
            if cat_ids:
                filters.append(('category_id', 'in', cat_ids))
        filters.append(('disattivato', '=', False))
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


    def print_registro(self, cr, uid, ids, context=None):
        asset_obj = self.pool['account.asset.asset']
        param = self.browse(cr, uid, ids[0])
        filters = []
        data = {}
        if param.cat_id:
            filters.append(('category_id', '=', param.cat_id.id))
        if param.lineap_id:
            filters.append(('lineap_id', '=', param.lineap_id.id))
        if param.sede_id:
            filters.append(('sede_id', '=', param.sede_id.id))
        if param.asset_type != 'A':
            cat_ids = self.pool.get('account.asset.category').search(
                cr, uid, [('asset_type', '=', param.asset_type)])
            if cat_ids:
                filters.append(('category_id', 'in', cat_ids))
        filters.append(('disattivato', '=', False))
        asset_ids = asset_obj.search(cr, uid, filters)
        #import pdb;pdb.set_trace()
        if asset_ids:
            ok = self.pool.get('asset.registro.temp').crea_temp(cr, uid,
                                                               asset_ids,
                                                               param)
            if ok:
                return self._print_registro_report(cr, uid, ids, data, param,
                                          context=context)
            else:
                raise osv.except_osv(_('Error'),
                                     _("No data to print"))
        else:
            raise osv.except_osv(_('Error'),
                                 _("No data to print"))
        return {'type': 'ir.actions.act_window_close'}

    def _print_registro_report(self, cr, uid, ids, data, parametri, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = {}
        return {'type': 'ir.actions.report.xml',
                'report_name': 'RegistroCespiti',
                'datas': data,
                }

asset_journal_wz()

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
               # 'asset_value_residual': fields.float('Asset Residual Value'),
                'type_amortization': fields.selection(
                    (('O', 'ordinary'),
                     ('F', 'first year reduction'),
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
                'lineap_id': fields.many2one('lineap.asset', 'Linea'),
                'sede_id': fields.many2one('asset.sedi', 'Sede'),

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
                # ('date_invoice', '>=', param.fiscal_year.date_start),
                ('date_invoice', '<=', param.fiscal_year.date_stop)])
            if not id_line_dep and not id_line_invoice \
                    and not param.not_moved_too:
                print_asset = False
            if not id_line_dep and not id_line_invoice \
                    and param.not_moved_too:
                if asset.purchase_date <= param.fiscal_year.date_stop:
                    print_asset = True
                else:
                    print_asset = False
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
                        'value_residual': line_dep.amount + line_dep.remaining_value,
                       # 'asset_value_residual': asset.value_residual,
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
                        if asset.sale_date:
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
                                'value_residual': 0.0, #asset.value_residual,
                                'type_amortization': asset.type_amortization,
                                'perc_ammortization': perc,
                                'depreciated_value': 0.0, #asset.value_residual,
                                'amount': 0.0,
                                'remaining_value': 0.0,
                                'sale_date': asset.sale_date,
                            }

                        else:
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
                                'perc_ammortization': 0.0,
                                'depreciated_value': 0.0, #asset.value_residual,
                                'amount': 0.0, #asset.amount,
                                'remaining_value': asset.remaining_value,
                                'sale_date': asset.sale_date,
                            }
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
                    vals['lineap_id'] = asset.lineap_id.id or False
                    vals['sede_id'] = asset.sede_id.id or False
                    self.create(cr, uid, vals)
                    ok = True
        return ok

asset_journal_temp()


class asset_registro_temp(osv.osv_memory):

    _name = 'asset.registro.temp'
    _description = 'TMP registro cespiti'

    def _pulisci(self, cr, uid, context=None):
        ids = self.search(cr, uid, [])
        self.unlink(cr, uid, ids, context)
        return True

    _columns = {'date': fields.date('Data di Stampa'),
                'fiscal_year': fields.many2one('account.fiscalyear',
                                               'Anno di Stampa'),
                'asset_type': fields.selection(
                    (('M', 'Material asset'),
                     ('I', 'Intangible asset'),
                     ('P', 'Capital gain'),
                     ('A', 'All')),
                    'Tipo Cespite'),
                'cat_id': fields.many2one('account.asset.category',
                                          'Categoria Selezione'),
                'first_page_number': fields.float('Da Pagina'),
                'not_moved_too': fields.boolean('Assets Without Moves'),
                'lineap_id': fields.many2one('lineap.asset', 'Linea'),
                'sede_id': fields.many2one('asset.sedi', 'Sede'),
                'asset_id': fields.many2one('account.asset.asset', 'Asset'),
                'category_id': fields.many2one('account.asset.category',
                                               'Categoria Cespite'),
                'purchase_date': fields.date('Purchase Date'),
                'purchase_value': fields.float('Gross Value'),
                'deductibility': fields.float('Deducibilita'),
                'sale_date': fields.date('Sale Date'),
                'im_non_amm': fields.float('Importo non Ammortizzabile'),
                'in_perc_amm': fields.float('Perc.Amm.to ini'),
                'ese_disatt': fields.char('Anno Disatt.', size=4),
                'fl_usato': fields.char('Usato', size=1),
                'in_type_amortization': fields.char('Tipo Ammortamento ini', size=20),
                'in_valbene': fields.float('Inc.Val.Bene ini'),
                'in_spese': fields.float('Oneri e Spese ini'),
                'in_rival': fields.float('Rivalutazioni ini'),
                'in_sval': fields.float('Svalutazioni ini'),
                'in_decval': fields.float('Dec.Val.Bene ini'),
                'in_fdoammord': fields.float('F.do Amm.to Ord. ini'),
                'in_fdoammant': fields.float('F.do Amm.to Ant. ini'),
                'in_quoper': fields.float('Quote Perse ini'),
                'in_resam': fields.float('Residuo da Amm. Ini'),
                'inv_line_id': fields.many2one('account.invoice.line', 'Riga Fattura'),
                'move_line_id': fields.many2one('account.move.line', 'Riga Registrazione'),
                'data_reg': fields.date('Data Registrazione'),
                'journal_id': fields.many2one('account.journal', 'Causale'),
                'partner_id': fields.many2one('res.partner', 'Fornitore / Cliente'),
                'numdoc': fields.char('Numero Documento', size=20),
                'data_doc': fields.date('Data Documento'),
                'importo': fields.float('Importo'),
                'fi_perc_amm': fields.float('Perc.Amm.to fin'),
                'fi_type_amortization': fields.char('Tipo Ammortamento fin', size=20),
                'fi_valbene': fields.float('Inc.Val.Bene fin'),
                'fi_spese': fields.float('Oneri e Spese fin'),
                'fi_rival': fields.float('Rivalutazioni Fin'),
                'fi_sival': fields.float('Svalutazioni Fin'),
                'fi_decval': fields.float('Dec.Val.Bene Fin'),
                'fi_fdoammord': fields.float('F.do Amm.to Ord. Fin'),
                'fi_fdoammant': fields.float('F.do Amm.to Ant. Fin'),
                'fi_quoper': fields.float('Quate Perse Fin'),
                'fi_resam': fields.float('Residuo da Amm. Fin'),

                }
    _order = "category_id,asset_id,data_reg"

    def find_last_year(self,cr, uid, ids, param, context=None):
        last_year = False
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        dtp = param.fiscal_year.date_stop
        anno = str(int(dtp[:4])-1)
        dt = anno + dtp[4:]
        last_year_ids = fiscalyear_obj.find(cr,uid,dt=dt)
        if last_year_ids:
            last_year = fiscalyear_obj.browse(cr,uid,last_year_ids)
        return last_year

    def crea_temp(self, cr, uid, ids, param, context=None):
        asset_obj = self.pool.get('account.asset.asset')
        asset_dep_lineobj = self.pool.get('account.asset.depreciation.line')
        invoice_lineobj = self.pool.get('account.invoice.line')
        move_lineobj =  self.pool.get('account.move.line')
        last_year = self.find_last_year(cr,uid,ids,param)
        ok = self._pulisci(cr, uid, context)
        ok = True

        if not ids:
            return False
        for asset in asset_obj.browse(cr, uid, ids):
            # cerca la riga di ammortamento dell'anno selezionato
            id_line_dep = asset_dep_lineobj.search(cr, uid, [
                ('asset_id', '=', asset.id),
                ('fiscal_year', '=', param.fiscal_year.id)])
            # cerca le righe fatture dell'anno selezionato
            id_line_invoice = invoice_lineobj.search(cr, uid, [
                ('asset_id', '=', asset.id),
                ('date_invoice', '>=', param.fiscal_year.date_start),
                ('date_invoice', '<=', param.fiscal_year.date_stop)])
            # se entrambe i risultati sono vuoti e non vuole i non movimentati 'print_asset' False
            if not id_line_dep and not id_line_invoice \
                    and not param.not_moved_too:
                print_asset = False
            # se entrambe sono vuoti e vuole i non movimentatiti
            # controlla che la data di acquisto sia inferiore alla data di fine esercizio
            # altrimenti quel cespite comunque non esiste in quell' esercizio
            if not id_line_dep and not id_line_invoice \
                    and param.not_moved_too:
                if asset.purchase_date <= param.fiscal_year.date_stop:
                    print_asset = True
                else:
                    print_asset = False
            if id_line_dep or id_line_invoice:
                # va comunque stampato
                print_asset = True
            if print_asset:
                # calcolo lo stato del cespite
                #import pdb;
                #pdb.set_trace()
                stato = ''
                if asset.value_residual != 0.0 and\
                     asset.accumulated_depreciation == 0.0 and\
                     asset.remaining_value == asset.value_residual:
                    stato = 'new'
                if asset.value_residual != 0.0 and\
                     asset.accumulated_depreciation != 0.0 and\
                     asset.remaining_value != asset.value_residual and\
                     asset.remaining_value != 0.0:
                    stato = 'doing'
                if asset.value_residual != 0.0 and\
                     asset.accumulated_depreciation == asset.value_residual and\
                     asset.remaining_value == 0.0:
                    stato = 'ended'
                if not id_line_dep and stato in ('new', 'doing'):
                    if stato == 'doing':
                        raise osv.except_osv(_('ERRORE !'),
                                             _('al cespite ' + asset.code + ' manca l ammortamento per il periodo richiesto'))
                    if stato == 'new':
                        if param.fiscal_year.id == asset.first_use_year.id:
                            raise osv.except_osv(_('ERRORE !'),
                                                 _('al cespite ' + asset.code + ' manca l ammortamento per il periodo richiesto'))
                testa_rec = {
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
                }
                # ora si cerca e calcola i dati iniziali
                if id_line_dep:
                    line_dep = asset_dep_lineobj.browse(cr, uid,
                                                        id_line_dep[0])
                else:
                    line_dep = False
                if last_year:
                    id_lline_dep = asset_dep_lineobj.search(cr, uid, [
                        ('asset_id', '=', asset.id),
                        ('fiscal_year', '=', last_year.id)])
                    if id_lline_dep:
                        last_line_dep = asset_dep_lineobj.browse(cr, uid,
                                                            id_lline_dep[0])
                    else:
                        last_line_dep = False
                else:
                    last_line_dep = False
                if last_line_dep:
                    testa_rec['in_valbene'] = asset.purchase_valuelast_line_dep.amount+last_line_dep.remaining_value
                    testa_rec['in_perc_amm'] = last_line_dep.perc_ammortization
                    testa_rec['in_fdoammord'] = last_line_dep.amount
                    testa_rec['in_type_amortization'] = last_line_dep.type_amortization
                else:
                    # vanno gestiti bene i casi in cui sono completamente ammortizzati
                    # questi dati a zero sono validi solo nel caso
                    # di primo ammortamento
                    testa_rec['in_valbene'] = 0.0
                    testa_rec['in_perc_amm'] = 0.0
                    testa_rec['in_fdoammord'] = 0.0
                    testa_rec['in_type_amortization'] = ''
                if line_dep:
                    testa_rec['fi_valbene'] = line_dep.amount+line_dep.remaining_value
                    testa_rec['fi_perc_amm'] = line_dep.perc_ammortization
                    testa_rec['fi_fdoammord'] = line_dep.amount
                    testa_rec['fi_type_amortization'] = line_dep.type_amortization
                else:
                    testa_rec['fi_valbene'] = asset.value_residual
                    testa_rec['fi_perc_amm'] = 0
                    testa_rec['fi_fdoammord'] = asset.accumulated_depreciation
                    testa_rec['fi_type_amortization'] = ''
                mv = {}
                not_write = True
                if id_line_invoice:
                    # ci sono delle fatture nell'anno indicato
                    for line in invoice_lineobj.browse(cr,uid,id_line_invoice):
                        mv = {}
                        mv['inv_line_id'] = line.id
                        mv['move_line_id'] = False
                        mv['data_reg'] = line.invoice_id.registration_date
                        mv['data_doc'] = line.invoice_id.date_invoice
                        mv['numdoc'] = line.invoice_id.supplier_invoice_number or line.invoice_id.number
                        mv['journal_id'] = line.invoice_id.journal_id.id
                        mv['partner_id'] = line.invoice_id.partner_id.id
                        mv['importo'] = line.price_subtotal
                        if line.invoice_id.type in ('out_invoice', 'in_refund'):
                            # deve decrementare il valore del bene
                            importo = line.price_subtotal * -1
                        else:
                            # fattura di acquisto o nc a cliente
                            importo = line.price_subtotal
                        record = testa_rec
                        record.update(mv)
                        self.create(cr, uid, record)
                        not_write = False
                else:
                    # non ci sono fatture per il periodo
                    pass
                if asset.account_move_line_ids:
                    testa_rec['partner_id'] = False
                    testa_rec['data_doc'] = False
                    testa_rec['numdoc'] = False
                    # if asset.code == 'AS/000007':
                    #     import pdb;pdb.set_trace()
                    for move_line in asset.account_move_line_ids:
                        mv = {}
                        if move_line.move_id.period_id.fiscalyear_id.id == param.fiscal_year.id:
                            mv['inv_line_id'] = False
                            mv['move_line_id'] = move_line.id
                            mv['data_reg'] = move_line.date
                            mv['journal_id'] = move_line.journal_id.id
                            mv['importo'] = move_line.debit
                            record = testa_rec
                            record.update(mv)
                            self.create(cr, uid, record)
                            not_write = False
                else:
                    # non ci sono movimenti per il periodo
                    pass

                if not_write:
                    record = testa_rec
                    self.create(cr, uid, record)

        return ok
# class asset_registro_total_temp(osv.osv_memory):
#
#     _name = 'asset.registro.total.temp'
#     _description = 'Totale calcolato per a stampa'
#
#     def _pulisci(self, cr, uid, context=None):
#         ids = self.search(cr, uid, [])
#         self.unlink(cr, uid, ids, context)
#         return True
#
#     _columns = {
#         'asset_id': fields.many2one('account.asset.asset', 'Asset'),
#         'fi_perc_amm': fields.float('Perc.Amm.to fin'),
#         'fi_type_amortization': fields.char('Tipo Ammortamento fin', size=20),
#         'fi_valbene': fields.float('Inc.Val.Bene fin'),
#         'fi_spese': fields.float('Oneri e Spese fin'),
#         'fi_rival': fields.float('Rivalutazioni Fin'),
#         'fi_sival': fields.float('Svalutazioni Fin'),
#         'fi_decval': fields.float('Dec.Val.Bene Fin'),
#         'fi_fdoammord': fields.float('F.do Amm.to Ord. Fin'),
#         'fi_fdoammant': fields.float('F.do Amm.to Ant. Fin'),
#         'fi_quoper': fields.float('Quate Perse Fin'),
#         'fi_resam': fields.float('Residuo da Amm. Fin'),
#     }
    def correggi_2016(self, cr, uid, ids, param, context=None):
        print 'Inizio controllo'
        asset_obj = self.pool.get('account.asset.asset')
        asset_dep_lineobj = self.pool.get('account.asset.depreciation.line')
        if not ids:
            return {'type': 'ir.actions.act_window_close'}
        if param.fiscal_year.code != '2016':
            raise osv.except_osv(_('Errore'),
                                 _("Periodo Errato"))
            return {'type': 'ir.actions.act_window_close'}
        id_line_dep = asset_dep_lineobj.search(cr, uid, [
            ('fiscal_year', '=', param.fiscal_year.id)])
        for line in asset_dep_lineobj.browse(cr, uid,id_line_dep):
            asset_dep_lineobj.write(cr, uid, [line.id],{
                'remaining_value': line.asset_id.purchase_value - line.depreciated_value
            })
            print line.asset_id.code, line.asset_id.purchase_value - line.depreciated_value


        return {'type': 'ir.actions.act_window_close'}
