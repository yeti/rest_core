import json
from rest_framework.test import APITestCase
import settings

__author__ = 'baylee'


class APITestCaseWithAssertions(APITestCase):
    """
    Taken from Tastypie's tests (https://github.com/toastdriven/django-tastypie/blob/master/tastypie/test.py)
    to improve readability
    """
    def assertHttpOK(self, resp):
        """
        Ensures the response is returning a HTTP 200.
        """
        return self.assertEqual(resp.status_code, 200)

    def assertHttpCreated(self, resp):
        """
        Ensures the response is returning a HTTP 201.
        """
        return self.assertEqual(resp.status_code, 201)

    def assertHttpAccepted(self, resp):
        """
        Ensures the response is returning either a HTTP 202 or a HTTP 204.
        """
        return self.assertIn(resp.status_code, [202, 204])

    def assertHttpMultipleChoices(self, resp):
        """
        Ensures the response is returning a HTTP 300.
        """
        return self.assertEqual(resp.status_code, 300)

    def assertHttpSeeOther(self, resp):
        """
        Ensures the response is returning a HTTP 303.
        """
        return self.assertEqual(resp.status_code, 303)

    def assertHttpNotModified(self, resp):
        """
        Ensures the response is returning a HTTP 304.
        """
        return self.assertEqual(resp.status_code, 304)

    def assertHttpBadRequest(self, resp):
        """
        Ensures the response is returning a HTTP 400.
        """
        return self.assertEqual(resp.status_code, 400)

    def assertHttpUnauthorized(self, resp):
        """
        Ensures the response is returning a HTTP 401.
        """
        return self.assertEqual(resp.status_code, 401)

    def assertHttpForbidden(self, resp):
        """
        Ensures the response is returning a HTTP 403.
        """
        return self.assertEqual(resp.status_code, 403)

    def assertHttpNotFound(self, resp):
        """
        Ensures the response is returning a HTTP 404.
        """
        return self.assertEqual(resp.status_code, 404)

    def assertHttpMethodNotAllowed(self, resp):
        """
        Ensures the response is returning a HTTP 405.
        """
        return self.assertEqual(resp.status_code, 405)

    def assertHttpConflict(self, resp):
        """
        Ensures the response is returning a HTTP 409.
        """
        return self.assertEqual(resp.status_code, 409)

    def assertHttpGone(self, resp):
        """
        Ensures the response is returning a HTTP 410.
        """
        return self.assertEqual(resp.status_code, 410)

    def assertHttpUnprocessableEntity(self, resp):
        """
        Ensures the response is returning a HTTP 422.
        """
        return self.assertEqual(resp.status_code, 422)

    def assertHttpTooManyRequests(self, resp):
        """
        Ensures the response is returning a HTTP 429.
        """
        return self.assertEqual(resp.status_code, 429)

    def assertHttpApplicationError(self, resp):
        """
        Ensures the response is returning a HTTP 500.
        """
        return self.assertEqual(resp.status_code, 500)

    def assertHttpNotImplemented(self, resp):
        """
        Ensures the response is returning a HTTP 501.
        """
        return self.assertEqual(resp.status_code, 501)

    def assertValidJSONResponse(self, resp):
        """
        Given a ``HttpResponse`` coming back from using the ``client``, assert that
        you get back:

        * An HTTP 200
        * The correct content-type (``application/json``)
        """
        self.assertHttpOK(resp)
        self.assertTrue(resp['Content-Type'].startswith('application/json'))


class ManticomTestCase(APITestCaseWithAssertions):
    def setUp(self):
        super(ManticomTestCase, self).setUp()

        # Parse schema objects for use later
        self.schema_objects = {}
        with open(settings.MANTICOM_SCHEMA) as file:
            schema_data = json.loads(file.read())
            for schema_obj in schema_data["objects"]:
                self.schema_objects.update(schema_obj)

    def check_schema_keys(self, data_object, schema_fields):
        """
            `data_object` is the actual JSON being sent or received
            `schema_fields` is the expected JSON based on the schema file
        """
        required_fields = []

        for schema_field, schema_type in schema_fields.iteritems():
            # If this field is actually another related object, then check that object's fields as well
            schema_parts = schema_type.split(',')
            is_list = False
            is_optional = False
            new_schema_object = None
            for part in schema_parts:
                # Parse through all parts, regardless of ordering
                if part == "array":
                    is_list = True
                elif part == "optional":
                    is_optional = True
                elif part.startswith('$'):
                    new_schema_object = part

            if not is_optional:
                required_fields.append(schema_field)

            if new_schema_object:
                if schema_field not in data_object or data_object[schema_field] is None:
                    # If our new object to check is None and optional then continue, else raise an error
                    if is_optional:
                        continue
                    else:
                        raise self.failureException("No data for object {0}".format(new_schema_object))

                new_data_object = data_object[schema_field]
                if is_list:
                    # If our new object to check is a list of these objects, continue if we don't have any daa
                    # Else grab the first one in the list
                    if len(new_data_object) == 0:
                        continue
                    new_data_object = new_data_object[0]

                self.check_schema_keys(new_data_object, self.schema_objects[new_schema_object])

        # The actual `data_object` contains every required field
        self.assertTrue(set(required_fields).issubset(set(data_object)))

        # The actual `data_object` contains no extraneous fields not found in the schema
        self.assertTrue(set(data_object).issubset(set(schema_fields)))

    def add_credentials(self, user):
        if user:
            token = user.accesstoken_set.first()
            self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token.token)
        else:
            self.client.credentials()

    def check_response_data(self, response, keypath, response_object_name):
        results_data = response.data
        if 'count' in results_data:  # If a list is returned, process looking for the first item
            results_data = results_data[keypath]
            if len(results_data) == 0:
                raise self.failureException("No data to compare response")
            results_data = results_data[0]
        self.check_schema_keys(results_data, self.schema_objects[response_object_name])

    def assertManticomGETResponse(
            self,
            url,
            parameters,
            response_object_name,
            user,
            unauthorized=False,
            keypath="results"
    ):
        """
        Runs a GET request and checks the GET parameters and results match the manticom schema
        """
        self.add_credentials(user)
        response = self.client.get(url, parameters)

        if unauthorized:
            self.assertHttpUnauthorized(response)
        else:
            self.assertValidJSONResponse(response)
            self.check_response_data(response, keypath, response_object_name)

        return response

    def assertManticomPOSTResponse(
            self,
            url,
            request_object_name,
            response_object_name,
            data,
            user,
            unauthorized=False,
            keypath="results"
    ):
        """
        Runs a POST request and checks the POST data and results match the manticom schema
        :rtype : object
        """
        self.check_schema_keys(data, self.schema_objects[request_object_name])

        self.add_credentials(user)
        response = self.client.post(url, data)

        if unauthorized:
            self.assertHttpUnauthorized(response)
        else:
            self.assertHttpCreated(response)
            self.assertTrue(response['Content-Type'].startswith('application/json'))
            self.check_response_data(response, keypath, response_object_name)

        return response

    def assertManticomPATCHResponse(self):
        pass

    def assertManticomDELETEResponse(self):
        pass

    def assertPhotoUpload(self):
        pass

    def assertVideoUpload(self):
        pass
