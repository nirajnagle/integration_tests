# -*- coding: utf-8 -*-
from copy import copy

from widgetastic.exceptions import NoSuchElementException
from widgetastic.widget import Text, Checkbox, View, ConditionalSwitchableView
from widgetastic_patternfly import Input, Button, BootstrapSelect, BootstrapSwitch, FlashMessages

from cfme.exceptions import ConsoleNotSupported, ConsoleTypeNotSupported
from cfme.utils import conf
from cfme.utils.appliance import NavigatableMixin
from cfme.utils.appliance.implementations.ui import navigate_to
from cfme.utils.log import logger
from cfme.utils.pretty import Pretty
from cfme.utils.update import Updateable


AUTH_MODES = {
    'database': 'Database',
    'ldap': 'LDAP',
    'ldaps': 'LDAPS',
    'amazon': 'Amazon',
    'external': 'External (httpd)'}

USER_TYPES = {
    'upn': 'User Principal Name',
    'email': 'E-mail Address',
    'cn': 'Distinguished Name (CN=<user>)',
    'uid': 'Distinguished Name (UID=<user>)',
    'sam': 'SAM Account Name'
}


class ServerInformationView(View):
    """ Class represents full Server tab view"""
    title = Text("//div[@id='settings_server']/h3[1]")
    # Local Flash widget for validation since class nested under a class inheriting BaseLoggedInPage
    flash = FlashMessages('.//div[@id="flash_msg_div"]/div[@id="flash_text_div" or '
                          'contains(@class, "flash_text_div")] | '
                          './/div[starts-with(@class, "flash_text_div") or @id="flash_text_div"]')
    save = Button('Save')
    reset = Button('Reset')

    @View.nested
    class basic_information(View):  # noqa
        """ Class represents Server Basic Information Form """
        hostname = Text(locator='.//label[normalize-space(.)="Hostname"]/../div')
        company_name = Input(name='server_company')
        appliance_name = Input(name='server_name')
        appliance_zone = BootstrapSelect(id='server_zone')
        time_zone = BootstrapSelect(id='server_timezone')
        locale = BootstrapSelect(id='locale')

    @View.nested
    class server_roles(View):  # noqa
        """ Class represents Server Roles Form """

        embedded_ansible = BootstrapSwitch(name='server_roles_embedded_ansible')
        ems_metrics_coordinator = BootstrapSwitch(name="server_roles_ems_metrics_coordinator")
        ems_operations = BootstrapSwitch(name="server_roles_ems_operations")
        ems_metrics_collector = BootstrapSwitch(name="server_roles_ems_metrics_collector")
        reporting = BootstrapSwitch(name="server_roles_reporting")
        ems_metrics_processor = BootstrapSwitch(name="server_roles_ems_metrics_processor")
        scheduler = BootstrapSwitch(name="server_roles_scheduler")
        smartproxy = BootstrapSwitch(name="server_roles_smartproxy")
        database_operations = BootstrapSwitch(name="server_roles_database_operations")
        smartstate = BootstrapSwitch(name="server_roles_smartstate")
        event = BootstrapSwitch(name="server_roles_event")
        user_interface = BootstrapSwitch(name="server_roles_user_interface")
        web_services = BootstrapSwitch(name="server_roles_web_services")
        ems_inventory = BootstrapSwitch(name="server_roles_ems_inventory")
        notifier = BootstrapSwitch(name="server_roles_notifier")
        automate = BootstrapSwitch(name="server_roles_automate")
        rhn_mirror = BootstrapSwitch(name="server_roles_rhn_mirror")
        database_synchronization_role = BootstrapSwitch(
            name="server_roles_database_synchronization")
        git_owner = BootstrapSwitch(name="server_roles_git_owner")
        websocket = BootstrapSwitch(name="server_roles_websocket")
        cockpit_ws = BootstrapSwitch(name="server_roles_cockpit_ws")
        # STORAGE OPTIONS
        storage_metrics_processor = BootstrapSwitch(name="server_roles_storage_metrics_processor")
        storage_metrics_collector = BootstrapSwitch(name="server_roles_storage_metrics_collector")
        storage_metrics_coordinator = BootstrapSwitch(
            name="server_roles_storage_metrics_coordinator")
        storage_inventory = BootstrapSwitch(name="server_roles_storage_inventory")
        vmdb_storage_bridge = BootstrapSwitch(name="server_roles_vmdb_storage_bridge")

        default_smart_proxy = Text(
            "//label[contains(text(), 'Default Repository SmartProxy')]/following-sibling::div")

    @View.nested
    class vmware_console(View):  # noqa
        """ Class represents Server VWware Console Support Form """

        console_type = BootstrapSelect("console_type")

    @View.nested
    class ntp_servers(View):  # noqa
        """ Class represents Server VWware Console Support Form """

        ntp_server_1 = Input(name="ntp_server_1")
        ntp_server_2 = Input(name="ntp_server_2")
        ntp_server_3 = Input(name="ntp_server_3")

    @View.nested
    class smtp_server(View):  # noqa
        """ Class represents SMTP Server Form """

        host = Input("smtp_host")
        port = Input("smtp_port")
        domain = Input("smtp_domain")
        start_tls = Input("smtp_enable_starttls_auto")
        ssl_verify = BootstrapSelect("smtp_openssl_verify_mode")
        auth = BootstrapSelect("smtp_authentication")
        username = Input("smtp_user_name")
        password = Input("smtp_password")
        from_email = Input("smtp_from")
        to_email = Input("smtp_test_to")
        verify = Button('Verify')

    @View.nested
    class web_services(View):  # noqa
        """ Class represents Server WebServices Form """

        mode = BootstrapSelect(id='webservices_mode')
        security = BootstrapSelect(id='webservices_security')

    @View.nested
    class logging_form(View):  # noqa
        """ Class represents Server Logging Form """

        log_level = BootstrapSelect(id='log_level')

    @View.nested
    class custom_support_url(View):  # noqa
        """ Class represents Server Custom Support URL Form """

        url = Input(name='custom_support_url')
        description = Input(name='custom_support_url_description')

    @property
    def is_displayed(self):
        return (
            self.basic_information.appliance_name.is_displayed and
            self.title.text == 'Basic Information')


class ServerInformation(Updateable, Pretty):
    """ This class represents the Server tab in Server Settings

    Different Forms take different values for their operations

    Note: All lower parameters by default set to None

    * BasicInformationForm:

        * company_name: [BasicInformationForm] Company name, default value in "My Company"
        * appliance_name: [BasicInformationForm] Appliance name.
        * appliance_zone: [BasicInformationForm] Appliance Zone.
        * time_zone: [BasicInformationForm] Time Zone.
        * locale: [BasicInformationForm] Locale used for users UI

    * ServerControlForm (Server Roles):

        * websocket, ems_metrics_coordinator, cockpit_ws, smartproxy,
        * storage_metrics_collector, database_operations, smartstate, event,
        * storage_inventory, storage_metrics_processor, web_services, automate,
        * rhn_mirror, database_synchronization, ems_operations, ems_metrics_collector,
        * reporting, ems_metrics_processor, scheduler, git_owner, user_interface,
        * embedded_ansible, storage_metrics_coordinator, ems_inventory,
        * vmdb_storage_bridge, notifier: set True/False to change the state

    * VWwareConsoleSupportForm:

        * console_type - Server console type

    * NTPServersForm:

        * ntp_server_1, ntp_server_2, ntp_server_3 - Set ntp server

    * SMTPServerForm:

        * host: SMTP Server host name
        * port: SMTP Server port
        * domain: E-mail domain
        * start_tls: Whether use StartTLS
        * ssl_verify: SSL Verification
        * auth: Authentication type
        * username: User name
        * password: User password
        * from_email: E-mail address to be used as the "From:"
        * test_email: Destination of the test-email.

    * WebServicesForm:

        * mode: web services mode
        * security: security type

    * LoggingForm:

        * log_level: log level type

    * CustomSupportURL:

        * url: custom url
        * decryption: url description
    """
    CONSOLE_TYPES = ('VNC', 'VMware VMRC Plugin', 'VMware WebMKS')
    SERVER_ROLES = ('embedded_ansible', 'ems_metrics_coordinator', 'ems_operations',
                    'ems_metrics_collector', 'reporting', 'ems_metrics_processor', 'scheduler',
                    'smartproxy', 'database_operations', 'smartstate', 'event', 'user_interface',
                    'web_services', 'ems_inventory', 'notifier', 'automate',
                    'rhn_mirror', 'database_synchronization_role', 'git_owner', 'websocket',
                    'storage_metrics_processor', 'storage_metrics_collector',
                    'storage_metrics_coordinator', 'storage_inventory', 'vmdb_storage_bridge',
                    'cockpit_ws')

    _basic_information = ['hostname', 'company_name', 'appliance_name', 'appliance_zone',
                          'time_zone', 'locale']
    _vmware_console = ['console_type']
    _ntp_servers = ['ntp_server_1', 'ntp_server_2', 'ntp_server_3']
    _smtp_server = ['host', 'port', 'domain', 'start_tls', 'ssl_verify', 'auth', 'username',
                   'password', 'from_email', 'to_email']
    _web_services = ['mode', 'security']
    _logging = ['log_level']
    _custom_support_url = ['url', 'description']

    pretty_attrs = ['appliance']

    def __init__(self, appliance):
        self.appliance = appliance
        full_form = (self._basic_information + list(self.SERVER_ROLES) + self._vmware_console +
                     self._ntp_servers + self._smtp_server + self._web_services + self._logging +
                     self._custom_support_url)
        for att in full_form:
            setattr(self, att, None)

# ============================= Basic Information Form =================================

    def update_basic_information(self, updates, reset=False):
        """ Navigate to a Server Tab. Updates basic information form

        Args:
             updates: dict, widgets will be updated regarding updates.
                ex. update_basic_information({'company_name': 'New name'})
             regarding updates.
             reset: By default(False) changes will not be reset, if True changes will be reset
        """
        view = navigate_to(self.appliance.server, 'Server')

        updated = view.basic_information.fill(updates)
        self._save_action(view, updated, reset)

    @property
    def basic_information_values(self):
        """ Returns(dict): basic_information fields values"""
        view = navigate_to(self.appliance.server, 'Server')
        return view.basic_information.read()

# =============================== Server Roles Form ===================================

    def update_server_roles_ui(self, updates, reset=False):
        """ Navigate to a Server Tab. Updates server roles via UI

        Args:
             updates: dict, widgets will be updated regarding updates.
             reset: By default(False) changes will not be reset, if True changes will be reset

        """
        view = navigate_to(self.appliance.server, 'Server')
        # embedded_ansible server role available from 5.8 version
        if self.appliance.version < '5.8' and 'embedded_ansible' in updates:
            updates.pop('embedded_ansible')

        # cockpit_ws element introduced in 5.9 version
        if self.appliance.version < 5.9 and 'cockpit_ws' in updates:
            updates.pop('cockpit_ws')
        updated = view.server_roles.fill(updates)
        self._save_action(view, updated, reset)

    def update_server_roles_db(self, roles):
        """ Set server roles on Configure / Configuration pages.

        Args:
            roles: Roles specified as in server_roles dict in this module. Set to True or False
        """
        if self.server_roles_db == roles:
            logger.debug(' Roles already match, returning...')
            return
        else:
            self.appliance.server_roles = roles

    @property
    def server_roles_db(self):
        """ Get server roles from Configure / Configuration from DB

        Returns: :py:class:`dict` ex.{'cockpit': True}
        """
        return self.appliance.server_roles

    @property
    def server_roles_ui(self):
        view = navigate_to(self.appliance.server, 'Server')
        roles = view.server_roles.read()
        # default_smart_proxy is not a role, but text info
        roles.pop('default_smart_proxy')
        return roles

    def enable_server_roles(self, *roles):
        """ Enables Server roles """
        self._change_server_roles_state(True, *roles)

    def disable_server_roles(self, *roles):
        """ Disable Server roles """
        self._change_server_roles_state(False, *roles)

    def _change_server_roles_state(self, enable, *roles):
        """ Takes care of setting required roles

        Args:
            enable: Whether to enable the roles.
        """
        try:
            original_roles = self.server_roles_db
            set_roles = copy(original_roles)
            for role in roles:
                set_roles[role] = enable
            self.update_server_roles_db(set_roles)
        except Exception:
            self.update_server_roles_db(original_roles)


# ============================= VMware Console Form =================================

    def update_vmware_console(self, updates, reset=False):
        """ Navigate to a Server Tab. Updates Vmware console

        Args:
             updates: dict, widgets will be updated regarding updates.
             reset: By default(False) changes will not be reset, if True changes will be reset

        """
        for name, value in updates.items():
            if name == 'console_type':
                if value not in self.CONSOLE_TYPES:
                    raise ConsoleTypeNotSupported(value)
                if self.appliance.version < '5.8':
                    raise ConsoleNotSupported(
                        product_name=self.appliance.product_name,
                        version=self.appliance.version
                    )
                # From 5.8 version need to add WebMKS_SDK
                if value == 'VMware WebMKS':
                    self.appliance.ssh_client.run_command('curl {} -o WebMKS_SDK.zip'.format(
                        conf.cfme_data.vm_console.webmks_console.webmks_sdk_download_url))

                    self.appliance.ssh_client.run_command('unzip -o ~/WebMKS_SDK.zip -d {}'.format(
                        conf.cfme_data.vm_console.webmks_console.webmks_sdk_extract_location))

        view = navigate_to(self.appliance.server, 'Server')
        view.browser.refresh()
        updated = view.vmware_console.fill(updates)
        self._save_action(view, updated, reset)

    @property
    def vmware_console_values(self):
        """ Returns(dict): vmware_console fields values"""
        view = navigate_to(self.appliance.server, 'Server')
        return view.vmware_console.read()

# ============================= NTP Servers Form =================================

    def update_ntp_servers(self, updates, reset=False):
        """ Navigate to a Server Tab. Updates ntp servers

        Args:
             updates: dict, widgets will be updated regarding updates.
             reset: By default(False) changes will not be reset, if True changes will be reset

        """
        view = navigate_to(self.appliance.server, 'Server')
        updated = view.ntp_servers.fill(updates)
        self._save_action(view, updated, reset)

    @property
    def ntp_servers_values(self):
        """ Returns(dict): ntp_servers fields values"""
        view = navigate_to(self.appliance.server, 'Server')
        return view.ntp_servers.read()

    @property
    def ntp_servers_fields_keys(self):
        """ Returns(list): ntp servers fields names"""
        return self._ntp_servers


# ============================= SMTP Server Form =================================

    def update_smtp_server(self, updates, reset=False):
        """ Navigate to a Server Tab. Updates smtp server

        Args:
             updates: dict, widgets will be updated regarding updates.
             reset: By default(False) changes will not be reset, if True changes will be reset
        """
        view = navigate_to(self.appliance.server, 'Server')
        try:
            updated = view.smtp_server.fill(updates)
        except Exception:
            # workaround for 5.7 version as sometimes throws Exception
            view = navigate_to(self.appliance.server, 'Server', use_resetter=True)
            updated = view.smtp_server.fill(updates)
        if view.smtp_server.verify.active:
            view.smtp_server.verify.click()
        self._save_action(view, updated, reset)

    def send_test_email(self, email=None):
        """ Send a testing e-mail on specified address. Needs configured SMTP. """
        view = navigate_to(self.appliance.server, 'Server')
        if not email:
            email = self.to_email
        view.smtp_server.fill({'to_email': email})
        view.smtp_server.verify.click()

    @property
    def smtp_server_values(self):
        """ Returns(dict): smtp_server fields values"""
        view = navigate_to(self.appliance.server, 'Server')
        return view.smtp_server.read()

# ============================= Web Services Form =================================

    def update_web_services(self, updates, reset=False):
        """ Navigate to a Server Tab. Updates web services

        Args:
             updates: dict, widgets will be updated regarding updates.
             reset: By default(False) changes will not be reset, if True changes will be reset
        """
        view = navigate_to(self.appliance.server, 'Server')
        updated = view.web_services.fill(updates)
        self._save_action(view, updated, reset)

    @property
    def web_services_values(self):
        """ Returns(dict): web_services fields values"""
        view = navigate_to(self.appliance.server, 'Server')
        return view.web_services.read()

# ============================= Logging Form =================================

    def update_logging_form(self, updates, reset=False):
        """ Navigate to a Server Tab. Updates logging form

        Args:
             updates: dict, widgets will be updated regarding updates.
             reset: By default(False) changes will not be reset, if True changes will be reset
        """
        view = navigate_to(self.appliance.server, 'Server')
        updated = view.web_services.fill(updates)
        self._save_action(view, updated, reset)

    @property
    def logging_values(self):
        """ Returns(dict): logging fields values"""
        view = navigate_to(self.appliance.server, 'Server')
        return view.logging_form.read()

# ============================= Custom Support Url Form =================================

    def update_custom_support_url(self, updates, reset=False):
        """ Navigate to a Server Tab. Updates custom support url

        Args:
             updates: dict, widgets will be updated regarding updates.
             reset: By default(False) changes will not be reset, if True changes will be reset
        """
        view = navigate_to(self.appliance.server, 'Server')
        updated = view.custom_support_url.fill(updates)
        self._save_action(view, updated, reset)

    @property
    def custom_support_url_values(self):
        """ Returns(dict): custom_support_url fields values"""
        view = navigate_to(self.appliance.server, 'Server')
        return view.custom_support_url.read()

    def _save_action(self, view, updated_result, reset):
        """ Take care of actions to do after updates """
        if reset:
            try:
                view.reset.click()
                view.flash.assert_message('All changes have been reset')
            except Exception:
                logger.warning('No values was changed')
        elif updated_result:
            view.save.click()
            view.flash.assert_no_error()
        else:
            logger.info('Settings were not changed')


# ============================= AUTHENTICATION TAB ===================================

class DatabaseAuthenticationView(View):
    """ Database Authentication View, empty"""
    pass


class LdapAuthenticationView(View):
    """ Ldap Authentication View """

    host1 = Input(name='authentication_ldaphost_1')
    host2 = Input(name='authentication_ldaphost_2')
    host3 = Input(name='authentication_ldaphost_3')
    port = Input(name='authentication_ldapport')
    user_type = BootstrapSelect(id='authentication_user_type')
    domain_prefix = Input(name='authentication_domain_prefix')
    user_suffix = Input(name='authentication_user_suffix')
    # the role/checkbox names are backasswards
    # the div label is 'Get [...] Groups' and the input name is [...]_role
    get_roles = Checkbox(name='get_direct_groups')
    get_groups = Checkbox(name='ldap_role')
    follow_referrals = Checkbox(name='follow_referrals')
    base_dn = Input(name='authentication_basedn')
    bind_dn = Input(name='authentication_bind_dn')
    bind_password = Input(name='authentication_bind_pwd')
    validate = Button('Validate')


class LdapsAuthenticationView(LdapAuthenticationView):
    """ Ldaps Authentication View """
    pass


class AmazonAuthenticationView(View):
    """ Amazon Authentication View """

    access_key = Input(name='authentication_amazon_key')
    secret_key = Input(name='authentication_amazon_secret')
    # the div label is 'Get [...] Groups' and the input name is [...]_role
    get_groups = Checkbox(name='amazon_role')
    validate = Button('Validate')


class ExternalAuthenticationView(View):
    """ External Authentication View """

    enable_sso = Checkbox(name='sso_enabled')
    enable_saml = Checkbox(name='saml_enabled')
    # the div label is 'Get [...] Groups' and the input name is [...]_role
    get_groups = Checkbox(name='httpd_role')


class ServerAuthenticationView(View):
    """ Server Authentication View."""
    title = Text("//div[@id='settings_authentication']/h3[1]")
    # Local Flash widget for validation since class nested under a class inheriting BaseLoggedInPage
    flash = FlashMessages('.//div[@id="flash_msg_div"]/div[@id="flash_text_div" or '
                          'contains(@class, "flash_text_div")] | '
                          './/div[starts-with(@class, "flash_text_div") or @id="flash_text_div"]')
    hours_timeout = BootstrapSelect(id='session_timeout_hours')
    minutes_timeout = BootstrapSelect(id='session_timeout_mins')
    # TODO new button widget to handle buttons_on buttons_off divs
    save = Button(title='Save Changes')  # in buttons_on div
    reset = Button(title='Reset Changes')  # in buttons_on div

    @View.nested
    class form(View):  # noqa
        auth_mode = BootstrapSelect(id='authentication_mode')
        auth_settings = ConditionalSwitchableView(reference='auth_mode')

        auth_settings.register('Database', default=True, widget=DatabaseAuthenticationView)
        auth_settings.register('LDAP', widget=LdapAuthenticationView)
        auth_settings.register('LDAPS', widget=LdapsAuthenticationView)
        auth_settings.register('Amazon', widget=AmazonAuthenticationView)
        auth_settings.register('External (httpd)', widget=ExternalAuthenticationView)

    @property
    def is_displayed(self):
        """should be paired with a ServerView.in_server_settings in a nav.am_i_here"""
        return (
            self.form.auth_mode.is_displayed and
            self.title.text == 'Authentication')


class AuthenticationSetting(NavigatableMixin, Updateable, Pretty):
    """
        Represents Authentication Setting for CFME

        Args:
            auth_mode: authorization mode, default value 'Database'
                One of: 'Database', 'Ldap', 'Ldaps', 'Amazon', 'External'
    """

    pretty_attrs = ['auth_mode']

    def __init__(self, appliance):
        self.appliance = appliance

    @property
    def auth_mode(self):
        """Check UI confiuration of auth mode"""
        view = navigate_to(self.appliance.server, 'Authentication', wait_for_view=True)
        return view.form.auth_mode.read()

    @auth_mode.setter
    def auth_mode(self, new_mode):
        """Set the auth mode to Database or external with no other args"""
        if new_mode.capitalize() not in ['Database', 'External']:
            raise ValueError('Setting auth_mode directly only allows for Database and External')
        else:
            view = navigate_to(self.appliance.server, 'Authentication', wait_for_view=True)
            changed = view.form.auth_mode.fill(AUTH_MODES.get(new_mode))
            if changed:
                view.save.click()

    def set_session_timeout(self, hours=None, minutes=None):
        """
            Sets the session timeout of the appliance.

            Args:
                hours(str): timeout hours value
                minutes(str): timeout minutes value
            ex. auth_settings.set_session_timeout('0', '30')
        """
        view = navigate_to(self.appliance.server, 'Authentication', wait_for_view=True)
        updated = view.fill({
            "hours_timeout": hours,
            "minutes_timeout": minutes
        })
        if updated:
            view.save.click()
            # TODO move this flash message assert into new test and only assert no error
            flash_message = (
                'Authentication settings saved for {} Server "{} [{}]" in Zone "{}"'.format(
                    self.appliance.product_name,
                    self.appliance.server.name,
                    self.appliance.server.sid,
                    self.appliance.server.zone.name))
            view.flash.assert_message(flash_message)

    @property
    def auth_settings(self):
        """ Authentication view fields values

        Includes auth_mode
        """
        view = navigate_to(self.appliance.server, 'Authentication')
        settings = view.form.read()
        return settings

    @auth_settings.setter
    def auth_settings(self, values):
        """Authentication view field setting, just form fill, no auth_provider handling

        Includes auth_mode
        Args:
            values: dict with auth_mode and auth_settings keys
        """
        view = navigate_to(self.appliance.server, 'Authentication', wait_for_view=True)
        if view.form.fill(values):
            try:
                view.save.click()
            except NoSuchElementException:
                logger.exception('NoSuchElementException when trying to save auth settings. BZ '
                                 '1527239 prevents consistent form saving. Assuming auth settings '
                                 'unchanged')
                pass

    def configure(self, auth_mode=None, auth_provider=None, user_type=None, reset=False,
                  validate=True):
        """ Set up authentication mode

        Defaults to Database if auth_mode is none, uses auth_provider.as_fill_value()

        Args:
            auth_mode: key for AUTH_MODES, UI dropdown selection, defaults to Database if None
            auth_provider: authentication provider class from cfme.utils.auth
            user_type: key for USER_TYPES
            reset:  to reset all changes for the page.after filling
            validate: validate ldap/ldaps/amazon provider config bind_dn+password

        """
        # Don't call lower() on None, just use 'database'
        mode = AUTH_MODES.get(auth_mode.lower() if auth_mode else 'database')
        settings = None  # determine correct settings for mode selection
        if mode == AUTH_MODES['database']:
            # no other auth config settings
            logger.warning('auth_mode is Database, ignoring auth_provider')
        elif mode == AUTH_MODES['external']:
            # limited config in external mode
            # possible to configure external with no auth provider object (default UI options)
            settings = auth_provider.as_fill_external_value() if auth_provider else None
        elif auth_provider:
            # full provider config
            settings = auth_provider.as_fill_value(auth_mode=auth_mode, user_type=user_type)
        else:
            raise ValueError('You have tried to configure auth with unexpected settings: '
                             '%r on mode %r', auth_provider, auth_mode)

        view = navigate_to(self.appliance.server, 'Authentication', wait_for_view=True)
        changed = view.form.fill({'auth_mode': mode, 'auth_settings': settings})
        if reset:
            view.reset.click()
            view.flash.assert_message('All changes have been reset')
            # Can't save the form if nothing was changed
            logger.info('Authentication form reset, returning')
            return
        elif changed:
            if validate and mode not in [AUTH_MODES['database'], AUTH_MODES['external']]:
                view.form.auth_settings.validate.click()
                view.flash.assert_no_error()
            # FIXME BZ 1527239 This button goes disabled if a password field is 'changed' to same
            # on exception, log and continue
            # no exception - assert flash messages
            # all cases - assert no flash error
            try:
                view.save.click()
            except NoSuchElementException:
                logger.exception('NoSuchElementException when trying to save auth settings. BZ '
                                 '1527239 prevents consistent form saving. Assuming auth settings '
                                 'unchanged')
                pass
            else:
                # TODO move this flash message assert into test and only assert no error
                view.flash.assert_success_message(
                    'Authentication settings saved for {} Server "{} [{}]" in Zone "{}"'
                    .format(self.appliance.product_name, self.appliance.server.name,
                            self.appliance.server.sid, self.appliance.server.zone.name))
            finally:
                view.flash.assert_no_error()
        else:
            logger.info('No authentication settings changed, not saving form.')
