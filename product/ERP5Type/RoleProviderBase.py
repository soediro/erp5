##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
""" Implement a shared base for tools which provide roles.

$Id$
"""

from Globals import DTMLFile, InitializeClass
from AccessControl import ClassSecurityInfo
from Products.CMFCore.Expression import Expression
from Products.ERP5Type import _dtmldir

from RoleInformation import RoleInformation
from Permissions import ManagePortal

#from interfaces.portal_roles import RoleProvider as IRoleProvider


class RoleProviderBase:
    """ Provide RoleTabs and management methods for RoleProviders
    """

    #__implements__ = IRoleProvider

    security = ClassSecurityInfo()

    _roles = ()

    _roles_form = DTMLFile( 'editToolsRoles', _dtmldir )

    manage_options = ( { 'label' : 'Roles'
                       , 'action' : 'manage_editRolesForm'
                       }
                     , 
                     )

    #
    #   RoleProvider interface
    #
    security.declarePrivate( 'getRoleList' )
    def getRoleList( self, info=None ):
        """ Return all the roles defined by a provider.
        """
        return self._roles or ()

    #
    #   ZMI methods
    #
    security.declareProtected( ManagePortal, 'manage_editRolesForm' )
    def manage_editRolesForm( self, REQUEST, manage_tabs_message=None ):

        """ Show the 'Roles' management tab.
        """
        roles = []

        for a in self.getRoleList():

            a1 = {}
            a1['id'] = a.getId()    # The Role Id (ex. Assignor)
            a1['name'] = a.Title()  # The name of this role definition (ex. Assignor at company X)
            a1['category'] = a.getCategory() or [] # Category definition
            a1['base_category'] = a.getBaseCategory() # Base Category Definition
            a1['user'] = a.getUserExpression()
            a1['condition'] = a.getCondition()
            roles.append(a1)

        return self._roles_form( self
                                 , REQUEST
                                 , roles=roles
                                 , management_view='Roles'
                                 , manage_tabs_message=manage_tabs_message
                                 )

    security.declareProtected( ManagePortal, 'addRole' )
    def addRole( self
                 , id
                 , name
                 , user
                 , condition
                 , category
                 , base_category=()
                 , REQUEST=None
                 ):
        """ Add an role to our list.
        """
        if not name:
            raise ValueError('A name is required.')

        a_expr = user and Expression(text=str(user)) or ''
        c_expr = condition and Expression(text=str(condition)) or ''

        new_roles = self._cloneRoles()

        new_role = RoleInformation(     id=str(id)
                                      , title=str(name)
                                      , user=a_expr
                                      , condition=c_expr
                                      , category=category.split('\n')
                                      , base_category=base_category.split()
                                      )

        new_roles.append( new_role )
        self._roles = tuple( new_roles )

        if REQUEST is not None:
            return self.manage_editRolesForm(
                REQUEST, manage_tabs_message='Added.')

    security.declareProtected( ManagePortal, 'changeRoles' )
    def changeRoles( self, properties=None, REQUEST=None ):

        """ Update our list of roles.
        """
        if properties is None:
            properties = REQUEST

        roles = []

        for index in range( len( self._roles ) ):
            roles.append( self._extractRole( properties, index ) )

        self._roles = tuple( roles )

        if REQUEST is not None:
            return self.manage_editRolesForm(REQUEST, manage_tabs_message=
                                               'Roles changed.')

    security.declareProtected( ManagePortal, 'deleteRoles' )
    def deleteRoles( self, selections=(), REQUEST=None ):

        """ Delete roles indicated by indexes in 'selections'.
        """
        sels = list( map( int, selections ) )  # Convert to a list of integers.

        old_roles = self._cloneRoles()
        new_roles = []

        for index in range( len( old_roles ) ):
            if index not in sels:
                new_roles.append( old_roles[ index ] )

        self._roles = tuple( new_roles )

        if REQUEST is not None:
            return self.manage_editRolesForm(
                REQUEST, manage_tabs_message=(
                'Deleted %d role(s).' % len(sels)))

    security.declareProtected( ManagePortal, 'moveUpRoles' )
    def moveUpRoles( self, selections=(), REQUEST=None ):

        """ Move the specified roles up one slot in our list.
        """
        sels = list( map( int, selections ) )  # Convert to a list of integers.
        sels.sort()

        new_roles = self._cloneRoles()

        for idx in sels:
            idx2 = idx - 1
            if idx2 < 0:
                # Wrap to the bottom.
                idx2 = len(new_roles) - 1
            # Swap.
            a = new_roles[idx2]
            new_roles[idx2] = new_roles[idx]
            new_roles[idx] = a

        self._roles = tuple( new_roles )

        if REQUEST is not None:
            return self.manage_editRolesForm(
                REQUEST, manage_tabs_message=(
                'Moved up %d role(s).' % len(sels)))

    security.declareProtected( ManagePortal, 'moveDownRoles' )
    def moveDownRoles( self, selections=(), REQUEST=None ):

        """ Move the specified roles down one slot in our list.
        """
        sels = list( map( int, selections ) )  # Convert to a list of integers.
        sels.sort()
        sels.reverse()

        new_roles = self._cloneRoles()

        for idx in sels:
            idx2 = idx + 1
            if idx2 >= len(new_roles):
                # Wrap to the top.
                idx2 = 0
            # Swap.
            a = new_roles[idx2]
            new_roles[idx2] = new_roles[idx]
            new_roles[idx] = a

        self._roles = tuple( new_roles )

        if REQUEST is not None:
            return self.manage_editRolesForm(
                REQUEST, manage_tabs_message=(
                'Moved down %d role(s).' % len(sels)))

    #
    #   Helper methods
    #
    security.declarePrivate( '_cloneRoles' )
    def _cloneRoles( self ):

        """ Return a list of roles, cloned from our current list.
        """
        return map( lambda x: x.clone(), list( self._roles ) )
 
    security.declarePrivate( '_extractRole' )
    def _extractRole( self, properties, index ):

        """ Extract an RoleInformation from the funky form properties.
        """
        id             = str( properties.get( 'id_%d'          % index, '' ) )
        name           = str( properties.get( 'name_%d'        % index, '' ) )
        user           = str( properties.get( 'user_%d'      % index, '' ) )
        condition      = str( properties.get( 'condition_%d'   % index, '' ) )
        category       = properties.get( 'category_%d'    % index, '' ).split('\n')
        base_category  = properties.get( 'base_category_%d'     % index, ''  ).split()

        if not name:
            raise ValueError('A name is required.')

        if user is not '':
            user = Expression( text=user )

        if condition is not '':
            condition = Expression( text=condition )

        return RoleInformation( id=id
                                , title=name
                                , user=user
                                , condition=condition
                                , category=category
                                , base_category=base_category
                                )

InitializeClass(RoleProviderBase)
