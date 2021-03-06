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

    def assertHttpNotAllowed(self, resp):
        """
        Depending on how we purposefully reject a call (e.g., limiting methods, using permission classes, etc.,
        we may have a few different HTTP response codes. Bundling these together into a single assertion so that
        Manticom tests can be more flexible.
        """
        return self.assertIn(resp.status_code, [401, 403, 404, 405])

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
                if part in ["array", "O2M", "M2M"]:
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

    def check_response_data(self, response, response_object_name):
        results_data = response.data

        if "results" in response.data or isinstance(response.data, list):  # If multiple objects returned
            if "results" in response.data:
                results_data = response.data["results"]
            else:  # A plain list is returned, i.e. from a bulk update request
                results_data = response.data

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
            unauthorized=False
    ):
        """
        Runs a GET request and checks the GET parameters and results match the manticom schema
        """
        self.add_credentials(user)
        response = self.client.get(url, parameters)
        if unauthorized:
            self.assertHttpNotAllowed(response)
        else:
            self.assertValidJSONResponse(response)
            self.check_response_data(response, response_object_name)

        return response

    def assertManticomPOSTResponse(
            self,
            url,
            request_object_name,
            response_object_name,
            data,
            user,
            format="json",
            unauthorized=False,
            status_OK=False,
    ):
        """
        Runs a POST request and checks the POST data and results match the manticom schema
        """
        if isinstance(data, list):  # Check first object if this is a bulk create
            self.check_schema_keys(data[0], self.schema_objects[request_object_name])
        else:
            self.check_schema_keys(data, self.schema_objects[request_object_name])

        self.add_credentials(user)
        response = self.client.post(url, data, format=format)
        if unauthorized:
            self.assertHttpNotAllowed(response)
        elif status_OK:
            self.assertHttpOK(response)
        else:
            self.assertHttpCreated(response)
            self.assertTrue(response['Content-Type'].startswith('application/json'))
            self.check_response_data(response, response_object_name)

        return response

    def assertManticomPATCHResponse(self,
            url,
            request_object_name,
            response_object_name,
            data,
            user,
            format="json",
            unauthorized=False
    ):
        """
        Runs a POST request and checks the POST data and results match the manticom schema
        """
        self.check_schema_keys(data, self.schema_objects[request_object_name])

        self.add_credentials(user)
        response = self.client.patch(url, data, format=format)
        if unauthorized:
            self.assertHttpNotAllowed(response)
        else:
            self.assertHttpOK(response)
            self.assertTrue(response['Content-Type'].startswith('application/json'))
            self.check_response_data(response, response_object_name)

        return response

    def assertManticomPUTResponse(self,
            url,
            request_object_name,
            response_object_name,
            data,
            user,
            format="json",
            unauthorized=False,
            forbidden=False
    ):
        """
        Runs a PUT request and checks the PUT data and results match the manticom schema for bulk updates.
        Assumes that all objects sent in a bulk update are identical, and hence only checks that the first one
        matches the schema.
        """
        self.check_schema_keys(data[0], self.schema_objects[request_object_name])

        self.add_credentials(user)
        response = self.client.put(url, data, format=format)
        if forbidden:
            # Attempting to update an object that isn't yours means it isn't in the queryset. DRF reads this as
            # creating, not updating. Since we have the `allow_add_remove` option set to False, creating isn't
            # allowed. So, instead of being rejected with a 403, server returns a 400 Bad Request.
            self.assertHttpBadRequest(response)
        elif unauthorized:
            self.assertHttpUnauthorized(response)
        else:
            self.assertHttpOK(response)
            self.assertTrue(response['Content-Type'].startswith('application/json'))
            self.check_response_data(response, response_object_name)

        return response

    def assertManticomDELETEResponse(self,
                                     url,
                                     user,
                                     unauthorized=False):
        self.add_credentials(user)
        response = self.client.delete(url)

        if unauthorized:
            self.assertHttpNotAllowed(response)
        else:
            self.assertHttpAccepted(response)

        return response

    def assertPhotoUpload(self):
        pass

    def assertVideoUpload(
            self,
            url,
            obj_to_update,
            user,
            path_to_video,
            path_to_thumbnail,
            related_media_model=None,
            related_name=None,
            extra_http=None,
            unauthorized=False
    ):
        """
            Checks that the video is uploaded and saved
            If the model being 'updated' is not the model that actually stores files (e.g., there is a Media model that
            has a relation to the model being updated), pass that model and the keyword field on that model that relates
            to the model being updated
        """
        self.add_credentials(user)
        kwargs = {
            "data": {
                'video_file': open(settings.PROJECT_ROOT + path_to_video, 'rb')
            },
            'format': 'multipart'
        }
        response = self.client.post(url, **kwargs)

        if unauthorized:
            self.assertHttpForbidden(response)
        else:
            self.assertHttpCreated(response)
            self.assertTrue(response['Content-Type'].startswith('application/json'))

            # Check the video and thumbnail are saved
            if related_media_model and related_name:
                filters = {
                    related_name: obj_to_update
                }
                obj_to_update = related_media_model.objects.filter(**filters)[0]
            else:
                obj_to_update = obj_to_update.__class__.objects.get(pk=obj_to_update.pk)
            original_file_field_name = getattr(obj_to_update, "original_file_name", "original_file")
            original_file = getattr(obj_to_update, original_file_field_name)
            self.assertEqual(
                original_file.file.read(),
                open(settings.PROJECT_ROOT + path_to_video, 'r').read()
            )
            self.assertEqual(
                obj_to_update.thumbnail.file.read(),
                open(settings.PROJECT_ROOT + path_to_thumbnail, 'r').read()
            )
