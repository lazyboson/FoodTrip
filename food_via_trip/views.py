import uuid
from operator import itemgetter
import requests
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from food_via_trip.models import Location
from food_via_trip.serializers import LocationSerailizer


# Create your views here.

class LocationInfoList(APIView):

    def get(self, request):
        locations = Location.objects.all()
        serializer = LocationSerailizer(locations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GenerateLocationInfo(APIView):
    @staticmethod
    def post(request):

        """
        Find location info by address
            ---
            parameters:
               - name: address
                 description: your location address
                 required: true

        """
        if not request.data.get('address'):
            return Response("Please provide address!", status=status.HTTP_400_BAD_REQUEST)
        address = request.data.get('address')
        if Location.objects.filter(address=address).exists():
            location = Location.objects.get(address=address)
            return Response({'location_id' : location.location_id}, status=status.HTTP_200_OK)
        locationFromAddress = settings.GLOBAL_SETTINGS['LOCATION_BASE_URI'] + '?query=' + address
        header = {"User-agent": "curl/7.43.0", "Accept": "application/json",
                  "user_key": settings.GLOBAL_SETTINGS['USER_KEY']}
        response = requests.get(locationFromAddress, headers=header)
        if not response:
            return Response("Zomoto Api didn't responding", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # not storing entire data of the response just storing useful one
        resp_json_payload = response.json()['location_suggestions'][0]
        data = {'location_id': str(uuid.uuid4()), 'entity_id': resp_json_payload['entity_id'],
                'entity_type': resp_json_payload['entity_type'], 'lat': resp_json_payload['latitude'],
                'long': resp_json_payload['longitude'], 'address': address}
        serializer = LocationSerailizer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PopulateRestaurantWithFare(APIView):

    @staticmethod
    def get(request, location_id):
        print location_id
        if not location_id:
            return Response("Please provide id!", status=status.HTTP_400_BAD_REQUEST)
        if not Location.objects.filter(location_id=location_id).exists():
            return Response("ID doesn't exists", status=status.HTTP_404_NOT_FOUND)
        query = Location.objects.get(location_id=location_id)
        entity_id = query.entity_id
        entity_type = query.entity_type
        start_lat = query.lat
        start_long = query.long

        restaurants = settings.GLOBAL_SETTINGS['LOCATION_DETAILS_BASE_URI'] + '?entity_id=' + str(
            entity_id) + '&entity_type=' + str(entity_type)
        header = {"User-agent": "curl/7.43.0", "Accept": "application/json",
                  "user_key": settings.GLOBAL_SETTINGS['USER_KEY']}
        response = requests.get(restaurants, headers=header)
        if not response:
            return Response("Zomoto Api didn't responding", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        resp_json_payload = response.json()['best_rated_restaurant']
        result = []

        # fetch top 10 best rated restaurant
        for restaurant in resp_json_payload:
            name = restaurant['restaurant']['name']
            end_lat = restaurant['restaurant']['location']['latitude']
            end_long = restaurant['restaurant']['location']['longitude']
            rating = restaurant['restaurant']['user_rating']['aggregate_rating']

            calculateFare = settings.GLOBAL_SETTINGS[
                                'TAXI_FARE_BASE_URI'] + '?server_token=' + settings.GLOBAL_SETTINGS[
                                'SERVER_TOKEN'] + '&start_latitude=' + str(
                start_lat) + '&start_longitude=' + str(start_long) + '&end_latitude=' + str(
                end_lat) + '&end_longitude=' + str(end_long)

            try:
                api_response = requests.get(calculateFare)
                api_response_json_payload = api_response.json()
            except requests.exceptions.ConnectionError:
                return Response('Uber api not responding', status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            if api_response_json_payload:
                try:
                    # some times uber api behaves weired distance is too much 100 miles. Handling in try except
                    prices = api_response_json_payload['prices']
                    for price in prices:
                        # since pool is cheapest assuming that
                        if 'UberGo' in price['localized_display_name'].encode('utf8'):
                            result.append({'name': name, 'rating': rating, 'fare': price['low_estimate']})
                            break
                except Exception as e:
                    pass

        sorted_data = sorted(result, key=itemgetter('fare'))
        print result
        res = {'price_rating': sorted_data}
        return Response(res, status=status.HTTP_200_OK)
