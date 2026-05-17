# Tool Tax Report

Grade: **brutal**

| Metric | Value |
| --- | ---: |
| Tools | 1123 |
| Full tool tax | 250,603 est. tokens |
| Slim index | 40,031 est. tokens |
| Potential savings | 210,572 est. tokens (84.0%) |
| Worst tool | 436 est. tokens |

## Heaviest Tools

| Tool | Tax | Index | Source |
| --- | ---: | ---: | --- |
| `replaceApiextensionsV1CustomResourceDefinitionStatus` | 436 | 34 | `/tmp/tool-tax-public-scans/kubernetes-openapi.json/paths//apis/apiextensions.k8s.io/v1/customresourcedefinitions/{name}/status/put` |
| `replaceApiregistrationV1APIServiceStatus` | 436 | 34 | `/tmp/tool-tax-public-scans/kubernetes-openapi.json/paths//apis/apiregistration.k8s.io/v1/apiservices/{name}/status/put` |
| `replaceCertificatesV1beta1NamespacedPodCertificateRequestStatus` | 436 | 34 | `/tmp/tool-tax-public-scans/kubernetes-openapi.json/paths//apis/certificates.k8s.io/v1beta1/namespaces/{namespace}/podcertificaterequests/{name}/status/put` |
| `replaceNetworkingV1NamespacedIngressStatus` | 436 | 34 | `/tmp/tool-tax-public-scans/kubernetes-openapi.json/paths//apis/networking.k8s.io/v1/namespaces/{namespace}/ingresses/{name}/status/put` |
| `replaceResourceV1NamespacedResourceClaimStatus` | 436 | 34 | `/tmp/tool-tax-public-scans/kubernetes-openapi.json/paths//apis/resource.k8s.io/v1/namespaces/{namespace}/resourceclaims/{name}/status/put` |
| `replaceResourceV1beta1NamespacedResourceClaimStatus` | 436 | 34 | `/tmp/tool-tax-public-scans/kubernetes-openapi.json/paths//apis/resource.k8s.io/v1beta1/namespaces/{namespace}/resourceclaims/{name}/status/put` |
| `replaceResourceV1beta2NamespacedResourceClaimStatus` | 436 | 34 | `/tmp/tool-tax-public-scans/kubernetes-openapi.json/paths//apis/resource.k8s.io/v1beta2/namespaces/{namespace}/resourceclaims/{name}/status/put` |
| `replaceSchedulingV1alpha2NamespacedPodGroupStatus` | 436 | 34 | `/tmp/tool-tax-public-scans/kubernetes-openapi.json/paths//apis/scheduling.k8s.io/v1alpha2/namespaces/{namespace}/podgroups/{name}/status/put` |
| `replaceRbacAuthorizationV1NamespacedRoleBinding` | 434 | 32 | `/tmp/tool-tax-public-scans/kubernetes-openapi.json/paths//apis/rbac.authorization.k8s.io/v1/namespaces/{namespace}/rolebindings/{name}/put` |
| `replaceRbacAuthorizationV1NamespacedRole` | 434 | 32 | `/tmp/tool-tax-public-scans/kubernetes-openapi.json/paths//apis/rbac.authorization.k8s.io/v1/namespaces/{namespace}/roles/{name}/put` |
| `replaceApiextensionsV1CustomResourceDefinition` | 432 | 32 | `/tmp/tool-tax-public-scans/kubernetes-openapi.json/paths//apis/apiextensions.k8s.io/v1/customresourcedefinitions/{name}/put` |
| `replaceApiregistrationV1APIService` | 432 | 32 | `/tmp/tool-tax-public-scans/kubernetes-openapi.json/paths//apis/apiregistration.k8s.io/v1/apiservices/{name}/put` |
| `replaceAppsV1NamespacedDaemonSetStatus` | 432 | 34 | `/tmp/tool-tax-public-scans/kubernetes-openapi.json/paths//apis/apps/v1/namespaces/{namespace}/daemonsets/{name}/status/put` |
| `replaceAppsV1NamespacedDeploymentScale` | 432 | 34 | `/tmp/tool-tax-public-scans/kubernetes-openapi.json/paths//apis/apps/v1/namespaces/{namespace}/deployments/{name}/scale/put` |
| `replaceAppsV1NamespacedDeploymentStatus` | 432 | 34 | `/tmp/tool-tax-public-scans/kubernetes-openapi.json/paths//apis/apps/v1/namespaces/{namespace}/deployments/{name}/status/put` |
| `replaceAppsV1NamespacedReplicaSetScale` | 432 | 34 | `/tmp/tool-tax-public-scans/kubernetes-openapi.json/paths//apis/apps/v1/namespaces/{namespace}/replicasets/{name}/scale/put` |
| `replaceAppsV1NamespacedReplicaSetStatus` | 432 | 34 | `/tmp/tool-tax-public-scans/kubernetes-openapi.json/paths//apis/apps/v1/namespaces/{namespace}/replicasets/{name}/status/put` |
| `replaceAppsV1NamespacedStatefulSetScale` | 432 | 34 | `/tmp/tool-tax-public-scans/kubernetes-openapi.json/paths//apis/apps/v1/namespaces/{namespace}/statefulsets/{name}/scale/put` |
| `replaceAppsV1NamespacedStatefulSetStatus` | 432 | 34 | `/tmp/tool-tax-public-scans/kubernetes-openapi.json/paths//apis/apps/v1/namespaces/{namespace}/statefulsets/{name}/status/put` |
| `replaceAutoscalingV1NamespacedHorizontalPodAutoscalerStatus` | 432 | 34 | `/tmp/tool-tax-public-scans/kubernetes-openapi.json/paths//apis/autoscaling/v1/namespaces/{namespace}/horizontalpodautoscalers/{name}/status/put` |

## What To Do

- Do not always-load full schemas. Generate a slim index and lazy-load schemas.
- Progressive loading has high upside for this catalog.
- Use --max-tokens and --max-tool-tokens to catch schema creep in pull requests.
