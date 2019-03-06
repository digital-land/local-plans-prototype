from application.models import PlanningAuthority, LocalPlan

pla_no_lds_url = PlanningAuthority.query.filter(PlanningAuthority.local_scheme_url.is_(None))
pla_no_lds_documents = PlanningAuthority.query.filter(PlanningAuthority.local_scheme_url.isnot(None)).filter(~PlanningAuthority.emerging_plan_documents.any())
pla_no_local_plan = PlanningAuthority.query.filter(~PlanningAuthority.local_plans.any())
pla_plan_no_docs = LocalPlan.query.filter(~LocalPlan.plan_documents.any())


query_map = {'pla-no-lds-url': pla_no_lds_url,
             'pla-no-lds-docs': pla_no_lds_documents,
             'pla-no-local-plan': pla_no_local_plan,
             'local-plan-no-docs': pla_plan_no_docs
             }
