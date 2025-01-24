from rest_framework import serializers
from .models import AutoAcceptCheque, Processor
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

class AutoAcceptChequeSerializer(serializers.ModelSerializer):
    success_webhook = serializers.URLField(
        required=True,
        allow_null=False,
        allow_blank=False,
        help_text="Ссылка для отправки подтверждения успешного принятия чека."
    )
    redirect_url = serializers.URLField(
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="Ссылка для перенаправления."
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
            'redirect_url'
        ]
        read_only_fields = ['id', 'created_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Сумма должна быть положительным числом.")
        return value

    def validate(self, attrs):
        url_validator = URLValidator()

        # Обязательная проверка success_webhook
        try:
            url_validator(attrs['success_webhook'])
        except ValidationError:
            raise serializers.ValidationError({"success_webhook": "Недействительный URL для success_webhook."})

        # Условная проверка redirect_url
        if attrs.get('redirect_url'):
            try:
                url_validator(attrs['redirect_url'])
            except ValidationError:
                raise serializers.ValidationError({"redirect_url": "Недействительный URL для redirect_url."})
        return attrs

    def create(self, validated_data):
        cheque = AutoAcceptCheque.objects.create(**validated_data)
        return cheque
    
class SmsReceiverSerializer(serializers.Serializer):
    sender = serializers.CharField(max_length=20)
    text = serializers.CharField()
    device_token = serializers.CharField(max_length=255)

    def validate_device_token(self, value):
        if not Processor.objects.filter(device_token=value).exists():
            raise serializers.ValidationError("Неверный device_token.")
        return value