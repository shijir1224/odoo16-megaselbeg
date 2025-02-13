/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService, useOwnedDialogs } from "@web/core/utils/hooks";
import { getNextTabableElement, getPreviousTabableElement } from "@web/core/utils/ui";
import { usePosition } from "@web/core/position_hook";
import { AutoComplete } from "@web/core/autocomplete/autocomplete";
import { AnalyticDistribution } from "@analytic/components/analytic_distribution/analytic_distribution";
//import { AccountMoveFormRenderer } from '@account/components/account_move_form/account_move_form';
import { _lt } from "@web/core/l10n/translation";
const { Component, useState, useRef, useExternalListener, onWillUpdateProps, onWillStart, onPatched } = owl;

const PLAN_APPLICABILITY = {
    mandatory: _lt("Mandatory"),
    optional: _lt("Optional"),
}
const PLAN_STATUS = {
    invalid: _lt("Invalid"),
    ok: _lt("OK"),
}
console.log('aasdaasasdaanal');
export class AnalyticDistributionMW extends AnalyticDistribution {

    // Lifecycle
    /*
    async willStart() {
        if (this.editingRecord) {
            await this.fetchAllPlans(this.props);
        }
        await this.formatData(this.props);
    }*/


    analyticAccountDomain(groupId=null) {
		console.log('aasdaasasdaanal====================================================');
        let domain = [['id', 'not in', this.existingAnalyticAccountIDs]];
        if (this.props.record.data.company_id){
            domain.push(
                '|',
                ['company_id', '=', this.props.record.data.company_id[0]],
                ['company_id', '=', false]
            );
        }

        if (groupId) {
            domain.push(['root_plan_id', '=', groupId]);
            domain.push(['branch_id', '=', 36]);
        }
        return domain;
    }

    searchAnalyticDomain(searchTerm) {
        return [
            '|',
            ["name", "ilike", searchTerm],
            '|',
            ['code', 'ilike', searchTerm],
            ['partner_id', 'ilike', searchTerm],
        ];
    }

}
/*
AnalyticDistribution.template = "analytic.AnalyticDistribution";
AnalyticDistribution.supportedTypes = ["char", "text"];
AnalyticDistribution.components = {
    AutoComplete,
    TagsList,
}

AnalyticDistribution.fieldDependencies = {
    analytic_precision: { type: 'integer' },
}*/

//registry.category("fields").add("analytic_distribution", AnalyticDistribution);
