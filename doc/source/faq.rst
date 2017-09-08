Frequently Asked Questions (FAQ)
================================

Below you can find some answers to frequently asked questions:

* Where can I find the logs associated with rho?

  You can find logs associated with rho in the $XDG_DATA_HOME/rho or the
  default, ~/.local/share/rho.

* Where can I find configuration information associated with rho?

  You can find configuration information associated with rho in the
  $XDG_CONFIG_HOME/rho or the default, ~/.config/rho.

* Why is rho not returning the path of JBoss EAP?

  If Java is not installed on the remote system the two tasks for detecting EAP
  will not complete successfully and will not display EAP installation if they
  are present.
