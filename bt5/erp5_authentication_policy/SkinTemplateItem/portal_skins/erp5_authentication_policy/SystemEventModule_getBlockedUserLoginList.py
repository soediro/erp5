"""
  Return list of blocked user logins in a 'listbox' format
"""
from DateTime import DateTime
from Products.ZSQLCatalog.SQLCatalog import Query
from Products.ERP5Type.Document import newTempBase

portal = context.getPortalObject()
portal_preferences = portal.portal_preferences

blocked_user_login_list = []
all_blocked_user_login_dict = {}

now = DateTime()
one_second = 1/24.0/60.0/60.0
check_duration = portal_preferences.getPreferredAuthenticationFailureCheckDuration()
max_authentication_failures = portal_preferences.getPreferredMaxAuthenticationFailure()
check_time = now - check_duration*one_second

kw = {'portal_type': 'Authentication Event',
      'creation_date': Query(creation_date = check_time,
                             range='min'),
      'validation_state' : 'confirmed'}
failure_list = portal.portal_catalog(**kw)
for failure in failure_list:
  person = failure.getDestinationValue()
  if person not in all_blocked_user_login_dict.keys():
    all_blocked_user_login_dict[person] = []
  all_blocked_user_login_dict[person].append(failure)

# leave only ones that are blocked:
for person, failure_list in all_blocked_user_login_dict.items():
  if len(failure_list) >= max_authentication_failures:
    blocked_user_login_list.append(newTempBase(portal, 
                                               person.getTitle(), 
                                               **{'title': person.getTitle(),
                                                  'count':len(failure_list),
                                                  'reference': person.getReference(),
                                                  'url': person.absolute_url()}))
return blocked_user_login_list
