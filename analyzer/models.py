from django.db import models
from django.conf import settings


class ResumeSubmission(models.Model):
	"""Store a user's resume submission (file or text) and results."""
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
	resume_file = models.FileField(upload_to='resumes/', null=True, blank=True)
	resume_text = models.TextField(null=True, blank=True)
	target_role = models.CharField(max_length=255)

	# Analysis results (populated after processing)
	score = models.IntegerField(null=True, blank=True)
	skills = models.JSONField(null=True, blank=True)
	recommendations = models.JSONField(null=True, blank=True)

	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"ResumeSubmission(id={self.id}, user={self.user}, role={self.target_role})"
