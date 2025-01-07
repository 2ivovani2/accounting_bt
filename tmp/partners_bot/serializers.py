from rest_framework import serializers
from .models import AutoAcceptCheque
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

class AutoAcceptChequeSerializer(serializers.ModelSerializer):
    success_webhook = serializers.URLField(
        required=True,
        allow_null=False,
        allow_blank=False,
        help_text="Ссылка для отправки подтверждения успешного принятия чека."
    )
    fail_webhook = serializers.URLField(
        required=True,
        allow_null=False,
        allow_blank=False,
        help_text="Ссылка для отправки уведомления о неудаче принятия чека."
    )

    class Meta:
        model = AutoAcceptCheque
        fields = [
            'id',
            'hash',
            'amount',
            'description',
            'created_at',
            'success_webhook',
            'fail_webhook'
        ]
        read_only_fields = ['id', 'created_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Сумма должна быть положительным числом.")
        return value

    # Удаляем метод validate_description, чтобы сделать поле необязательным

    def validate(self, attrs):
        """
        Дополнительная валидация для webhook-ссылок, если необходимо.
        """
        url_validator = URLValidator()
        try:
            url_validator(attrs['success_webhook'])
        except ValidationError:
            raise serializers.ValidationError({"success_webhook": "Недействительный URL для success_webhook."})
        
        try:
            url_validator(attrs['fail_webhook'])
        except ValidationError:
            raise serializers.ValidationError({"fail_webhook": "Недействительный URL для fail_webhook."})

        return attrs

    def create(self, validated_data):
        # Здесь вы можете добавить дополнительную логику, если необходимо
        cheque = AutoAcceptCheque.objects.create(**validated_data)
        return cheque
    
class SmsReceiverSerializer(serializers.Serializer):
    sender = serializers.CharField(max_length=20)
    text = serializers.CharField()