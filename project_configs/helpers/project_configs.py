import os

from aws_cdk import Environment

from .helper import load_yamls, load_yamls_to_dict, load_bootstrap

# Load environment definitions
dirname = os.path.dirname(__file__)

#props_paths=f"../environment_options/environment_options.yaml"

props_paths = f"./{os.environ['props_paths']}"
props = (load_yamls(os.path.join(dirname, props_paths)))[0]


env_devsecops_account = Environment(account=props['devsecops_account'], region=props['devsecops_region'])

# load tags
#tags = (load_yamls(os.path.join(dirname,props_paths )))[1]['tags']
tags = props['tags']


for env in props['environment_props']:
    # Load Bootstrap
    bootstrap_commands = load_bootstrap(os.path.join(dirname, os.path.dirname(props_paths), env['bootstrap_commands']))
    env['bootstrap_commands'] = bootstrap_commands


