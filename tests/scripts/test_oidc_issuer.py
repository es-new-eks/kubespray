from pathlib import Path
import unittest

from jinja2 import Environment, StrictUndefined
import yaml


class OIDCIssuerTest(unittest.TestCase):
    def test_kubeadm_oidc_arguments(self):
        root = Path(__file__).resolve().parents[2]
        source = (root / "roles/kubernetes/control-plane/templates/kubeadm-config.v1beta4.yaml.j2").read_text()
        start = source.index("{% if kube_oidc_auth")
        end = source.index("{% if kube_apiserver_use_authentication_config_file %}")
        template = Environment(undefined=StrictUndefined).from_string(source[start:end])
        addresses = dict(kube_oidc_management_vip="192.0.2.10", kube_oidc_management_first_master="192.0.2.11")
        for inputs, expected in [
            ({}, None),
            (dict(kube_vip_address="192.0.2.91", first_kube_control_plane_address="192.0.2.92"), None),
            (dict(addresses, kube_oidc_url="https://id.example.org/dex"), "https://id.example.org/dex"),
            (dict(addresses, kube_oidc_fip="2001:db8::7", kube_oidc_port=30443), "https://[2001:db8::7]:30443"),
            (dict(addresses, kube_oidc_fip=" "), "https://192.0.2.10:32000"),
            (dict(addresses, kube_oidc_management_vip=None), "https://192.0.2.11:32000"),
            (dict(addresses, kube_oidc_auth=False), None),
            (dict(addresses, kube_apiserver_use_authentication_config_file=True), None),
        ]:
            with self.subTest(inputs=inputs):
                variables = dict(kube_oidc_auth=True, kube_oidc_client_id="kubernetes",
                                 kube_apiserver_use_authentication_config_file=False)
                variables.update(inputs)
                args = yaml.safe_load(template.render(variables)) or []
                self.assertEqual(args, [] if expected is None else [
                    {"name": "oidc-issuer-url", "value": expected},
                    {"name": "oidc-client-id", "value": "kubernetes"},
                ])


if __name__ == "__main__":
    unittest.main()
