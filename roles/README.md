# Centralized set of ansible roles

This contains all the roles that are used in multiple competitions.  Each
competition can include these roles in their top level `.yml` file, and then
add on their own customizations after as needed.  Generally, these roles
should be included before customizations, and there may be an order that
they need to be run in in order to run correctly (for example, mediawiki
must be run before a role installing an extension).

In general, the roles will install a file in the `torque-sites-config` folder
of the mediawiki instance, and then include that file in `LocalSettings.php`

* [activitylog/](activitylog/) - Checkout and installation of the 
  [Activity Log Extension](https://github.com/OpenTechStrategies/ActivityLog/).
  The checkout is made from github, rather than pulling down a tar.
* [collection/](collection/) - Deployment and installation of the
  [Collection Extension](https://www.mediawiki.org/wiki/Extension:Collection).
  This is used for book printing along with mwlib, and requres the
  [mwlib base](../base/mwlib) service to be installed.  The collection tar
  is kept locally to ensure availability.  There are also some patches to
  update the extension and enable some interfaces.
* [embed\_video/](embed_video/) - Installation of the
  [Embed Video Extension](https://www.mediawiki.org/wiki/Extension:EmbedVideo).
  The tar is kept locally for availability, and there are some patches for
  accessibility.
* [exporttables/](exporttables/) - Installation of the mediawiki side of the
  [Export Tables Extension](https://www.mediawiki.org/wiki/Extension:ExportTables).
  Also requires the installation of:
  * [ExtJSBase](https://www.mediawiki.org/wiki/Extension:ExtJSBase)
  * [BlueSpiceFoundation](https://www.mediawiki.org/wiki/Extension:BlueSpiceFoundation)
  * [BlueSpiceUniversalExport](https://www.mediawiki.org/wiki/Extension:UniversalExport)
  * [UEModuleTable2Excel](https://www.mediawiki.org/wiki/Extension:UEModuleTable2Excel)
  These are all kept locally to ensure availability.
* [finishmediawiki/](finishmediawiki/) - The final step that should be taken
  when deploying a site.  Updates the database and does any cleanup necessary.
* [mediawiki/](mediawiki/) - The second step that should be taken to deploy
  a completition.  Actually installs mediawiki and sets the foundation of the
  directory structure.
* [mysql/](mysql/) - Creates the user for the mediawiki instance in mysql.  Should
  often be run as its own host, as the mysql instance may not be on the same machine
  as the mediawiki instance.
* [permissions/](permissions/) - The default permissions for the macfound groups.
  While not all of these groups and permissions are enabled on all competitions,
  this is the baseline.  Local modifications of these permissions should appear
  in `LocalSettings.php` after the loading of this file, in order to make sure
  this does't overwrite.  See
  [the default-permissions file](permissions/files/default-permissions.php)
  for more documentation about the actual groups
* [picksome/](picksome/) - Checkout and installation of the
  [PickSome Extension](https://github.com/OpenTechStrategies/PickSome/)
* [postgres/](postgres/) - Create the user for the mediawiki instance in postgres.
  Like `mysql` role above, should be run as a separate host.
* [rss/](rss/) - Installation of the
  [RSS Extension](https://www.mediawiki.org/wiki/Extension:RSS).  Tar is kept locally
  for availability.
* [simplefavorites/](simplefavorites/) - Checkout and installation of the
  [Simple Favorites Extension](https://github.com/OpenTechStrategies/SimpleFavorites/)
* [simplesaml/](simplesaml/) - Installation of the mediawiki side of the simplesamlphp
  configuration.  Requres installing the [simplesamlphp base](../base/simplesaml) on
  the same machine that this is run on.  Installs, from local tars, both
  [Pluggable Auth Extension](https://www.mediawiki.org/wiki/Extension:PluggableAuth)
  and [SimpleSamlPHP Extension](https://www.mediawiki.org/wiki/Extension:SimpleSAMLphp).
  These are used to enable SSO via Okta in the competitions.
* [teamcomments/](teamcomments/) - Checkout and installation of the
  [Team Comments Extension](https://github.com/OpenTechStrategies/TeamComments/)
* [torquedataconnect/](torquedataconnect/) - Checkout and installation of
  the TorqueDataConnect extension from [torque](https://github.com/OpenTechStrategies/torque).
  Requires a running torque system to be [installed from base](../base/torque).  The
  checkout sha in this role does not necessarily need to match the checkout sha in the
  base directory.  The checkout doesn't happen in the extensions directory (unlike other
  extenstions above), but rather is symlinked from a checkout of the whole torque project.

See [../INSTALL.md](../INSTALL.md) for more information on how to configure your
system to pick up these roles.

