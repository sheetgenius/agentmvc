use loco_rs::{auth::jwt, hash, prelude::*};
use serde_json::Map;
use uuid::Uuid;

pub use super::_entities::users::{self, ActiveModel, Entity, Model};

#[async_trait::async_trait]
impl ActiveModelBehavior for ActiveModel {
    async fn before_save<C>(mut self, _db: &C, insert: bool) -> std::result::Result<Self, DbErr>
    where
        C: ConnectionTrait,
    {
        if insert {
            self.pid = Set(Uuid::new_v4());
        }
        Ok(self)
    }
}

impl Model {
    pub async fn by_username(
        db: &DatabaseConnection,
        username: &str,
    ) -> std::result::Result<Option<Self>, DbErr> {
        Entity::find()
            .filter(users::Column::Username.eq(username))
            .one(db)
            .await
    }

    pub async fn by_email(
        db: &DatabaseConnection,
        email: &str,
    ) -> std::result::Result<Option<Self>, DbErr> {
        Entity::find()
            .filter(users::Column::Email.eq(email))
            .one(db)
            .await
    }

    pub async fn by_pid(
        db: &DatabaseConnection,
        pid: &str,
    ) -> std::result::Result<Option<Self>, DbErr> {
        let Ok(pid) = Uuid::parse_str(pid) else {
            return Ok(None);
        };
        Entity::find()
            .filter(users::Column::Pid.eq(pid))
            .one(db)
            .await
    }

    pub async fn register(
        db: &DatabaseConnection,
        username: String,
        email: String,
        password: String,
    ) -> ModelResult<Self> {
        let password = hash::hash_password(&password).map_err(|e| ModelError::Any(e.into()))?;
        Ok(ActiveModel {
            username: Set(username),
            email: Set(email),
            password: Set(password),
            ..Default::default()
        }
        .insert(db)
        .await?)
    }

    pub fn token(&self, secret: &str, expiration: u64) -> ModelResult<String> {
        jwt::JWT::new(secret)
            .generate_token(expiration, self.pid.to_string(), Map::new())
            .map_err(ModelError::from)
    }

    pub fn verify_password(&self, password: &str) -> bool {
        hash::verify_password(password, &self.password)
    }
}

impl ActiveModel {
    pub async fn change_password(
        mut self,
        db: &DatabaseConnection,
        password: &str,
    ) -> ModelResult<Model> {
        self.password = Set(hash::hash_password(password).map_err(|e| ModelError::Any(e.into()))?);
        Ok(self.update(db).await?)
    }
}
