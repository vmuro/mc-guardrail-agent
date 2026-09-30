# Estágio 1: Build da aplicação Java com Maven
FROM eclipse-temurin:21-jdk-alpine AS builder

WORKDIR /build

# Copia arquivos do wrapper e POM para cache de dependências
COPY .mvn .mvn
COPY mvnw pom.xml ./
RUN chmod +x mvnw && ./mvnw dependency:go-offline -B || true

# Copia código-fonte e compila
COPY src ./src
RUN ./mvnw clean package -DskipTests

# Estágio 2: Imagem final enxuta de execução (JRE 21)
FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

# Usuário não-root para segurança
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# Copia o artefato compilado
COPY --from=builder /build/target/*.jar app.jar

# Porta padrão do Spring Boot
EXPOSE 8080

# Inicialização
ENTRYPOINT ["java", "-Djava.security.egd=file:/dev/./urandom", "-jar", "app.jar"]
