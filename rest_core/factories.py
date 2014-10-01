import factory
import datetime
from oauth2_provider.models import AccessToken
from videos.models import User


class UserFactory(factory.Factory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: 'person{0}@example.com'.format(n))
    username = factory.Sequence(lambda n: 'person{0}'.format(n))

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        user = super(UserFactory, cls)._create(model_class, *args, **kwargs)
        # Force save for post_save signal to create auth client
        user.save()
        AccessToken.objects.create(user=user,
                                   application=user.application_set.first(),
                                   token='token{}'.format(user.id),
                                   expires=datetime.datetime.utcnow() + datetime.timedelta(days=1)
        )
        return user
