from auth_client.graph_utils import GraphAPI
import auth_client

import configs

# setup auth client for azure ad flows
ad_client = auth_client.AuthClient(configs.CLIENT_ID, configs.CLIENT_SECRET, configs.TENANT_ID,
                                    mode="ad")

# setup auth client for azure ad b2c flows
ad_b2c_client = auth_client.AuthClient(configs.CLIENT_ID, configs.CLIENT_SECRET, configs.B2C_TENANT_NAME, 
                                        oauth_tenant_id=configs.TENANT_ID, user_flow=configs.B2C_FLOW_NAME)


graph_client = GraphAPI(client_id=configs.CLIENT_ID, tenant_id=configs.TENANT_ID, client_secret=configs.CLIENT_SECRET)
