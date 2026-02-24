import pytest
from django.urls import reverse
import json

@pytest.mark.django_db
def test_field_edit_success(auth_client, field):
    url = reverse("edit-field", kwargs={
        "tournament_id": field.tournament.id,
        "pk": field.id
    })

    response = auth_client.post(
        url,
        data=json.dumps({"name": "Updated Field"}),
        content_type="application/json"
    )

    assert response.status_code == 200
    field.refresh_from_db()
    assert field.name == "Updated Field"