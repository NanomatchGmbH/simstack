#  import requests
#  
#  
#  # Unicore REST API Documentation:
#  #   http://sourceforge.net/p/unicore/wiki/REST_API
#  #
#  # Support list:
#  # Base URL:
#  # /                                                       GET             y
#  # 
#  # Sites:
#  # /sites                                                  GET             y
#  # /sites                                                  POST            n
#  # /sites/{id}                                             GET             y
#  # /sites/{id}                                             DELETE          n
#  # /sites/{id}                                             POST            n
#  # /sites/{id}/jobs?offset={offset}&num={num}              GET             y
#  # /sites/{id}/applications                                GET             y 
#  # /sites/{id}/applications/{appID}                        GET             y
#  # 
#  # Storages:
#  # /storages                                               GET             y
#  # /storages                                               POST            n
#  # /storages/{id}                                          GET             y
#  # /storages/{id}                                          DELETE          y
#  # /storages/{id}/files/{filePath}                         GET             n
#  # /storages/{id}/files/{filePath}                         PUT             n
#  # /storages/{id}/files/{filePath}                         GET             n
#  # /storages/{id}/files/{filePath}                         PUT             n
#  # /storages/{id}/files/{filePath}                         DELETE          n
#  # /storages/{id}/imports                                  POST            n
#  # /storages/{id}/exports                                  POST            n
#  # /storages/{id}/transfers                                POST            n
#  # /storages/{id}/search?q=query-string                    GET             n
#  # 
#  # Jobs:
#  # /jobs                                                   GET             y
#  # /jobs                                                   POST            n
#  # /jobs/{id}                                              GET     
#  # /jobs/{id}                                              DELETE  
#  # /jobs/actions/start                                     POST    
#  # /jobs/actions/abort                                     POST    
#  # /jobs/actions/restart                                   POST    
#  
#  
#  # Test function:
#  # def query(url):
#  #     r = requests.get(url, cert=('2015-03-31_flo_test.crt', '2015-03-31_flo_test.key'), verify=False, auth=('flo_test','flo123test'))
#  #     print json.dumps(r.json(), indent=4)
#  # 
#  # curl --cert demo_user_unicore.crt.pem --key demo_user_unicore.key.pem -k -u flo_test:flo123test -H "Content-type: application/json" -X POST --data-binary @/tmp/testjob.u https://int-nanomatchcluster.int.kit.edu:8080/rest/core -i -v
#  
#  
#  class API:
#      def __init__(self, 
#                  baseUrl='https://int-nanomatchcluster.int.kit.edu:8080/NANO-SITE/rest/core',
#                  keypair=('2015-03-31_flo_test.crt', '2015-03-31_flo_test.key'),
#                  authType='basic',
#                  basicAuth=('user', 'password')
#              ):
#  
#      def connect():
#          """Connects to the given base URL and extracts general info about the
#          client and links to other resources.
#  
#          This queries 'BASE/'.
#          @returns true on success
#          """
#  
#      def get_sites():
#      def get_site():
#  
#      def get_storages():
#      def get_storage():
#  
#  class Application:
#      def __init__(self, name, version):
#          self.name = name
#          self.version = version
#  
#  class Site:
#      def __init__(self, id):
#          self.id = id                    # Site ID
#      def get_info():
#      def delete():
#      def submit_job():
#      def list_jobs(num=10, offset=0):
#      def get_applications():
#      def get_application():
#  
#  
#  def Storage:
#      def __init__(self, id):
#      def get_info():
#      def delete():
#  
